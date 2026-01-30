app_config = dict()

the_prefix = ''

def prefix(): 
    global the_prefix
    return the_prefix

def update_prefix(foo):
    global the_prefix
    the_prefix = foo

