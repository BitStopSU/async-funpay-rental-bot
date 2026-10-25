import json

from aioFunPayAPI import Account
from aioFunPayAPI import types
from aioFunPayAPI.common import exceptions
from bs4 import BeautifulSoup


class FunPayAccount(Account):
    """Keep the additional session cookie required by FunPay's event endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.golden_seal = None

    async def method(self, *args, **kwargs):
        response = await super().method(*args, **kwargs)
        self.golden_seal = response.get_dict().get("golden_seal") or self.golden_seal
        return response

    async def get(self, update_phpsessid: bool = False):
        await super().get(update_phpsessid=update_phpsessid)
        if self.phpsessid and self.golden_seal:
            self.phpsessid = f"{self.phpsessid}; golden_seal={self.golden_seal}"
        return self

    async def get_lot_fields(self, lot_id: int) -> types.LotFields:
        if not self.is_initiated:
            raise exceptions.AccountNotInitiatedError()
        response = await self.method(
            "get",
            f"lots/offerEdit?offer={int(lot_id)}",
            {
                "accept": "*/*",
                "content-type": "application/json",
                "x-requested-with": "XMLHttpRequest",
            },
            {},
            raise_not_200=True,
        )
        try:
            payload = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = None
        html = payload.get("html") if isinstance(payload, dict) else None
        if not html:
            html = response.text
        if not html or not html.strip():
            raise ValueError("FunPay returned an empty listing edit form")

        soup = BeautifulSoup(html, "html.parser")
        fields = {"active": "", "deactivate_after_sale": ""}
        fields.update({
            field["name"]: field.get("value") or ""
            for field in soup.find_all("input")
            if field.get("name") not in (None, "active", "deactivate_after_sale")
        })
        fields.update({
            field["name"]: field.text or ""
            for field in soup.find_all("textarea")
            if field.get("name")
        })
        for field in soup.find_all("select"):
            selected = field.find("option", selected=True)
            if field.get("name") and selected:
                fields[field["name"]] = selected.get("value", "")
        fields.update({
            field["name"]: "on"
            for field in soup.find_all("input", {"type": "checkbox"}, checked=True)
            if field.get("name")
        })
        return types.LotFields(int(lot_id), fields)
