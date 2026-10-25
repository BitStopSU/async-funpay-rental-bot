from aioFunPayAPI import Account


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
