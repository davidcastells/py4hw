from deprecated import deprecated

from .path import is_cygwin_path
from .path import is_windows_path
from .path import windows_to_cygwin

gVerbose = True

@deprecated(reason="use patch_edalize_for_vivado_project") 
def patch_edalize_for_project(project_dir, VIVADO_PATH, BASH):
    return patch_edalize_for_vivado_project(project_dir, VIVADO_PATH, BASH)
        
def patch_edalize_for_vivado_project(project_dir, VIVADO_PATH, BASH):
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
    
    
def patch_edalize_for_quartus_project(project_dir, QUARTUS_PATH, BASH, verbose=False):
    from edalize.build_runners.make import Make
    import edalize.quartus as quartus_tool
    from edalize.edatool import Edatool
    
    gVerbose = verbose
    
    if (gVerbose):
        print('PATCHING QUARTUS')
    
    if not(is_cygwin_path(project_dir)):
        project_dir = windows_to_cygwin(project_dir)

    if not(is_cygwin_path(QUARTUS_PATH)):
        WINDOWS_QUARTUS_PATH = QUARTUS_PATH
        QUARTUS_PATH = windows_to_cygwin(QUARTUS_PATH)


    if (hasattr(quartus_tool.Quartus, 'py4hw_patch')):
        print('Edalize was already patched for py4hw')
        return

    def my_get_build_command(self):
        if (gVerbose):
            print('BUILD OPTIONS:', self.build_options)
            
        return (BASH, ['-l', '-c', f'cd {project_dir};/bin/make']) 


    # _orig_setup = vivado_tool.Vivado.setup
    _orig_run_tool = Edatool._run_tool
    
    
    def patched_run_tool(self, cmd, *a, **kw):
        if (gVerbose):
            print('RUN:', cmd, a, kw)

        if cmd == 'make':
            args = kw.pop('args', a[0] if a else [])
            full_cmd = f'cd {project_dir}; /bin/make ' + ' '.join(args)
            # drop positional args, since args is now passed by keyword
            return _orig_run_tool(self, BASH, args=['-l', '-c', full_cmd], **kw)
        
        elif cmd == 'quartus_pgm':
            cmd = WINDOWS_QUARTUS_PATH + '\\quartus_pgm'
            
            tuple_a = a
            list_a = tuple_a[0]
            
            #for i in range(len(list_a)):
            #    param = list_a[i]
            #    if param.startswith('p;') and param.endswith('.sof'):
            #        param = 'p;output_files\\' + param[2:] + ''
            #        list_a[i] = param
                    
            
        return _orig_run_tool(self, cmd, *a, **kw)

    # vivado_tool.Vivado.setup = _patched_setup
    Make.get_build_command = my_get_build_command
    Edatool._run_tool = patched_run_tool

    from edalize.quartus import Quartus
    
    _orig_render = Quartus.render_template
    
    def patched_render(self, template_file, target_file, template_vars={}):
        if (gVerbose):
            print('RENDER TEMPLATE', template_file)
        import os
        _orig_render(self, template_file, target_file, template_vars)
        if template_file.endswith('makefile.j2') or 'makefile' in template_file:
            path = os.path.join(self.work_root, target_file)
            with open(path) as f:
                txt = f.read()
            txt = txt.replace('quartus_sh', QUARTUS_PATH + '/quartus_sh') 
            txt = txt.replace('quartus_map', QUARTUS_PATH + '/quartus_map') 
            txt = txt.replace('quartus_fit', QUARTUS_PATH + '/quartus_fit') 
            txt = txt.replace('quartus_sta', QUARTUS_PATH + '/quartus_sta') 
            txt = txt.replace('quartus_asm', QUARTUS_PATH + '/quartus_asm') 
            txt = txt.replace('quartus_dse', QUARTUS_PATH + '/quartus_dse') 
    
    
            with open(path, 'w') as f:
                f.write(txt)
    
            if (gVerbose):
                print('PATCHED makefile')
                print(txt)
                print()

    Quartus.render_template = patched_render
    quartus_tool.Quartus.py4hw_patch = True    
    