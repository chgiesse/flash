## Patch Log 

## _2024-11-08 - async path walk_  

### Dash
- enable_dev_tools 

### _watch
- watch 

### plugins
- dash_duo - replaced ThreadedRunner class with MultiProcessRunner for tests - multithreading had problems with the event loop

## _2024-11-08 - Initial Patch_
-
### Dash
- __ init __
- init_app
- serve_layout
- dependencies
- serve_reload_hash
- serve_component_suites
- dispatch
- enable_dev_tools
- run 
- enable_pages
- index
- _serve_default_favicon
- _setup_server

## Pages
- _create_redirect_function
- _infer_module_name 
- _page_meta_tags

## Callback
- _invoke_callback
- register_callback
- has_context

## Callback Context
- setup_props
- CallbackContext

## _configs
- pages_folder_config

## _validate
- validate_use_pages
