import asyncio
import aiohttp
from pyhiveapi import Session

token = '7e/HpjiVI320n4+bq7G9aepVPUfuwWsbEOROE114nLE='


async def main():
    async with aiohttp.ClientSession() as session:
        a = Session(session)
        return await a.start_session(30,
                                     token,
                                     None,
                                     None)


loop = asyncio.get_event_loop()

content = loop.run_until_complete(main())
print(content)
loop.close()
