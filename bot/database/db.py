import aiosqlite


class DB:
    def __init__(self):
        self.con = None

    async def on_startup(self):
        self.con = await aiosqlite.connect("database/user.db")

        await self.con.execute(
            "CREATE TABLE IF NOT EXISTS users(verifed TEXT, user_id BIGINT PRIMARY KEY, lang TEXT, amount TEXT, "
            "username TEXT, trader_id BIGINT)"
        )
        await self.con.execute("CREATE TABLE IF NOT EXISTS desc(ref TEXT)")
        await self.con.execute("CREATE TABLE IF NOT EXISTS promo(promo TEXT)")

        cursor = await self.con.execute("SELECT COUNT(*) FROM desc")
        count = await cursor.fetchone()
        if count[0] == 0:
            await self.con.execute("INSERT INTO desc(ref) VALUES (?)", ("https://primer.com/",))

        cursor = await self.con.execute("SELECT COUNT(*) FROM promo")
        count = await cursor.fetchone()
        if count[0] == 0:
            await self.con.execute("INSERT INTO promo(promo) VALUES (?)", ("TEXT",))

        await self.con.commit()

    async def close(self):
        if self.con:
            await self.con.close()

    async def get_ref(self) -> str:
        query = 'SELECT * FROM desc'
        result = await self.con.execute(query)
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return ""

    async def get_trader_id(self, user_id):
        query = "SELECT trader_id FROM users WHERE user_id = ?"
        async with self.con.execute(query, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]  # Возвращаем trader_id
        return None  # Если trader_id не найден

    async def add_trader_id(self, user_id, trader_id):
        query = "UPDATE users SET trader_id = ? WHERE user_id = ?"
        await self.con.execute(query, (trader_id, user_id))
        await self.con.commit()

    async def get_promo(self) -> str:
        query = 'SELECT * FROM promo'
        result = await self.con.execute(query)
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return ""

    async def edit_ref(self, url: str) -> None:
        current_ref = await self.get_ref()
        query = 'UPDATE desc SET ref = ? WHERE ref = ?'
        await self.con.execute(query, (url, current_ref))
        await self.con.commit()

    async def edit_promo(self, text: str) -> None:
        current_promo = await self.get_promo()
        if current_promo:
            query = 'UPDATE promo SET promo = ? WHERE promo = ?'
            await self.con.execute(query, (text, current_promo))
            await self.con.commit()

    async def get_users_count(self) -> int:
        query = "SELECT COUNT(*) FROM users"
        result = await self.con.execute(query)
        return (await result.fetchone())[0]

    async def get_verified_users_count(self) -> int:
        query = "SELECT COUNT(*) FROM users WHERE verifed = 'verifed'"
        result = await self.con.execute(query)
        return (await result.fetchone())[0]

    async def get_dep_users_count(self) -> int:
        query = "SELECT COUNT(*) FROM users WHERE amount = 'dep'"
        result = await self.con.execute(query)
        return (await result.fetchone())[0]

    async def register(self, user_id, language: str, username: str = "user", verifed="0", amount="0", trader_id=None):
        try:
            query = "INSERT INTO users(verifed, user_id, lang, amount, username, trader_id) VALUES(?, ?, ?, ?, ?, ?)"
            await self.con.execute(query, (verifed, user_id, language, amount, username, trader_id))
            await self.con.commit()
        except aiosqlite.IntegrityError:
            pass

    async def get_user(self, user_id):
        ver = "verifed"
        query = 'SELECT * FROM users WHERE user_id = ? AND verifed = ?'
        result = await self.con.execute(query, (user_id, ver))
        row = await result.fetchone()

        if row:
            return {
                'user_id': row[1],
                'verifed': row[0],
            }
        return None

    async def get_deposit_status(self, user_id):
        query = 'SELECT * FROM users WHERE user_id = ?'
        async with self.con.execute(query, (user_id,)) as cursor:
            row = await cursor.fetchone()

            if row:
                return {
                    'user_id': row[1],
                    'amount': row[3],
                }
        return None

    async def update_verifed(self, user_id, verifed="verifed"):
        query = "UPDATE users SET verifed = ? WHERE user_id = ?"
        await self.con.execute(query, (verifed, user_id))
        await self.con.commit()

    async def update_deposit_status(self, user_id, amount="dep"):
        query = 'UPDATE users SET amount = ? WHERE user_id = ?'
        await self.con.execute(query, (amount, user_id))
        await self.con.commit()

    async def get_user_info(self, user_id):
        query = 'SELECT * FROM users WHERE user_id = ?'
        result = await self.con.execute(query, (user_id,))
        return await result.fetchone()

    async def get_users(self):
        query = "SELECT * FROM users"
        result = await self.con.execute(query)
        return await result.fetchall()

    async def update_lang(self, user_id, language: str):
        query = "UPDATE users SET lang = ? WHERE user_id = ?"
        await self.con.execute(query, (language, user_id))
        await self.con.commit()

    async def get_lang(self, user_id):
        query = "SELECT lang FROM users WHERE user_id = ?"
        result = await self.con.execute(query, (user_id,))
        row = await result.fetchone()
        if row is not None:
            return row[0]
        return None

    async def get_user_data(self, user_input):
        user_input = str(user_input)

        if user_input.isdigit():
            cursor = await self.con.execute("SELECT * FROM users WHERE user_id = ?", (int(user_input),))
        else:
            cursor = await self.con.execute("SELECT * FROM users WHERE username = ?", (user_input,))

        user_data = await cursor.fetchone()
        await cursor.close()

        if user_data:
            return {
                "verifed": user_data[0],
                "user_id": user_data[1],
                "lang": user_data[2],
                "amount": user_data[3],
                "username": user_data[4]
            }
        else:
            return None


DataBase = DB()
