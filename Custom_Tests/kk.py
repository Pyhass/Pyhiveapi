import asyncio
import aiohttp
from pyhiveapi import Session, Hotwater

token = '7e/HpjiVI320n4+bq7G9aepVPUfuwWsbEOROE114nLE='


async def main():
    async with aiohttp.ClientSession() as session:
        a = Session(session)
        content = await a.start_session(30,
                                        token,
                                        None,
                                        None)
        device = content['water_heater'][0]
        return await Hotwater.get_hotwater(Hotwater(), device)


loop = asyncio.get_event_loop()

content = loop.run_until_complete(main())
print(content)
loop.close()
