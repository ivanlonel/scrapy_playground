from twisted.internet import task, reactor


async def async_sleep(delay, callable=None, *args, **kw):
    return await task.deferLater(reactor, delay, callable, *args, **kw)
