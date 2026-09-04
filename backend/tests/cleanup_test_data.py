"""Remove QA-created users/tips and recompute duel tip_counts."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values
from bson import ObjectId

env = dotenv_values("/app/backend/.env")


async def main():
    cl = AsyncIOMotorClient(env["MONGO_URL"])
    db = cl[env["DB_NAME"]]
    users = await db.users.find({"email": {"$regex": "^(test_|tester)", "$options": "i"}}).to_list(1000)
    ids = [str(u["_id"]) for u in users]
    print("removing users:", [u["email"] for u in users])
    if ids:
        await db.tips.delete_many({"user_id": {"$in": ids}})
        await db.users.delete_many({"_id": {"$in": [ObjectId(i) for i in ids]}})
    # also remove any QA duels
    await db.duels.delete_many({"shooter1": {"$regex": "^(TEST|QA) ", "$options": "i"}})
    # recompute tip counts
    async for d in db.duels.find({}):
        did = str(d["_id"])
        counts = {}
        for p in ("1", "X", "2"):
            counts[p] = await db.tips.count_documents({"duel_id": did, "pick": p})
        await db.duels.update_one({"_id": d["_id"]}, {"$set": {"tip_counts": counts}})
    print("duels:", await db.duels.count_documents({}), "users:", await db.users.count_documents({}), "tips:", await db.tips.count_documents({}))
    cl.close()


asyncio.run(main())
