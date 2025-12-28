import asyncio
from database.database import cleanup_old_messages

async def main():
    print("Cleaning up old messages...")
    deleted = await cleanup_old_messages()
    print(f"Cleaned up {deleted} old messages.")

if __name__ == "__main__":
    asyncio.run(main())
