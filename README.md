# Flash

#### *Flash is a Quart async Patch of Dash*.

`Flash` is a async patch of the [Plotly Dash](https://github.com/plotly/dash) library, building on Quart as backend instead of Flask. It is very inspired by the already existing [dash-async](https://github.com/snehilvj/async-dash) repo, but covering all **features up to Dash 2.18.2**

Quarts async capabilities are directly baked into the standard library, making it easy to inject into existing projects. 

Flash makes it possible to run **true async callbacks** and layout functions while running sync functions in a separate thread (_asyncio.run_in_executor_).

With [dash-extensions](https://www.dash-extensions.com/) you can create native websocket components and handle server side events making your application realtime compatible. 

#### Table Of Contents
- [Motivation]('#motivation')
- [Caveats](#caveats)
- [Known Issues](#known-issues)
- [TODO](#todo)

### Motivation
One of my biggest pain points in Dash was to handle database requests, forcing me to add quite alot callbacks to first fetch a lacy component and then render the real component when the ID of the lacy copmonent appeared. Often leading to quite complex pattern matching callbacks to fetch each components data. 


Now the DB requests dont block each other and alot interaction can be outsourced to the URL. In order to enhace further responsiveness i am thinking about to add a LazyLoad compoent ([more-infos]('#TODO'))

### Caveats
- background callbacks have run to sync
    - will be fixed in the future
    - sync callback gets put into a spearate exeuctor
- dash testings - dash_duo had to be changed to a multi process runner instead of a threaded runner
- somehow I can't turn of logs in dev mode

### Known Issues
- not all tests pass - detailed look in TEST_LOGS.md 
    - 10 integration tests
    - 2 unit tests
### TODO
- shared callbacks / channel callbacks like [dash-devices](https://github.com/richlegrand/dash_devices) offered. Will most likly be implemented with redis PubSub

- adding a LacyLoad component like [dash-grocery](https://github.com/IcToxi/dash-grocery), this will also increase responsiveness and overall better UI feeling
