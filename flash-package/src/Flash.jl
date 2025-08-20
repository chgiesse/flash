
module Flash
using Dash

const resources_path = realpath(joinpath( @__DIR__, "..", "deps"))
const version = "1.2.0"

include("jl/sse.jl")

function __init__()
    DashBase.register_package(
        DashBase.ResourcePkg(
            "flash",
            resources_path,
            version = version,
            [
                DashBase.Resource(
    relative_package_path = "async-SSE.js",
    external_url = "https://unpkg.com/flash@1.2.0/flash/async-SSE.js",
    dynamic = nothing,
    async = :true,
    type = :js
),
DashBase.Resource(
    relative_package_path = "async-SSE.js.map",
    external_url = "https://unpkg.com/flash@1.2.0/flash/async-SSE.js.map",
    dynamic = true,
    async = nothing,
    type = :js
),
DashBase.Resource(
    relative_package_path = "flash.js",
    external_url = nothing,
    dynamic = nothing,
    async = nothing,
    type = :js
),
DashBase.Resource(
    relative_package_path = "flash.js.map",
    external_url = nothing,
    dynamic = true,
    async = nothing,
    type = :js
)
            ]
        )

    )
end
end
