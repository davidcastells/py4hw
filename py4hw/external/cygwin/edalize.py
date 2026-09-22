from .path import is_cygwin_path
from .path import is_windows_path
from .path import windows_to_cygwin

def patch_edalize_for_project(project_dir, VIVADO_PATH, BASH):
    from edalize.build_runners.make import Make
    import edalize.tools.vivado as vivado_tool
    import edalize.flows.edaflow as edaflow_mod
    
    if not(is_cygwin_path(project_dir)):
        project_dir = windows_to_cygwin(project_dir)

    if not(is_cygwin_path(VIVADO_PATH)):
        VIVADO_PATH = windows_to_cygwin(VIVADO_PATH)

    if not(is_windows_path(BASH)):
        raise Exception(f'BASH should be a windows path, now = {BASH}')

    if (hasattr(vivado_tool.Vivado, 'py4hw_patch')):
        print('Edalize was already patched for py4hw')
        return

    def my_get_build_command(self):
        #print('BUILD OPTIONS:', self.build_options)
        return (BASH, ['-l', '-c', f'cd {project_dir};/bin/make']) 


    _orig_setup = vivado_tool.Vivado.setup
    _orig_run_tool = edaflow_mod.Edaflow._run_tool
    
    def _patched_setup(self, edam):
        _orig_setup(self, edam)
        for cmd in self.commands.commands:      # each is an EdaCommands.Command
            #print('CMD:', cmd)
            for subcmd in cmd.commands:         # each is an argv-style list
                #print('SUBCMD:', subcmd)
                if subcmd and subcmd[0] == "vivado":
                    subcmd[0] = VIVADO_PATH

    
    def patched_run_tool(self, cmd, *a, **kw):
        if cmd == "make":
            # pull out 'args' whether passed positionally or as a kwarg
            args = kw.get("args", a[0] if a else [])
            full_cmd = f"cd {project_dir};/bin/make " + " ".join(args)
            kw["args"] = ["-l", "-c", full_cmd]
    
            #print('RUN:', BASH, a, kw)
            return _orig_run_tool(self, BASH, *a[1:] if a else (), **kw)
    
        #print('RUN:', cmd, a, kw)
        return _orig_run_tool(self, cmd, *a, **kw)

    vivado_tool.Vivado.setup = _patched_setup
    Make.get_build_command = my_get_build_command
    edaflow_mod.Edaflow._run_tool = patched_run_tool

    vivado_tool.Vivado.py4hw_patch = True
    