import time
import os.path
import subprocess
import bakebit_128_64_oled as oled
import sys

from modules.pages.simpletable import SimpleTable

class App(object):

    def __init__(self, g_vars):
       
        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

   
    def profiler_ctl_file_update(self, fields_dict, filename):

        # read in file to an array
        with open(filename, 'r') as f:
            lines = f.readlines()

        # loop through each field in values to set in file
        for key, value in fields_dict.items():

            # step through all lines and look for a match
            for count, line in enumerate(lines):
                # replace match in file with key/value pair
                if line.startswith(key):
                    lines[count] = "{}: {}\n".format(key, value)
        
        # write modified file back out
        with open(filename, 'w') as f:
            f.writelines(lines)

        
    def profiler_running(self):
        try:
            # this cmd fails if process not active
            cmd = "systemctl is-active --quiet profiler.service"
            subprocess.check_output(cmd, shell=True)
            return True
        except subprocess.CalledProcessError as exc:
            return False
                
    def profiler_ctl(self, g_vars, action="status"):
        '''
        Function to start/stop and get status of Profiler processes
        '''
        # if we're been round this loop before, 
        # results treated as cached to prevent re-evaluating
        # and re-painting 
        if g_vars['result_cache'] == True:
           # re-enable keys
           g_vars['disable_keys'] = False
           return True
        
        # disable keys while we react to the key press that got us here
        g_vars['disable_keys'] = True

        # check resource is available
        try:
            # this cmd fails if service not installed
            cmd = "systemctl is-enabled profiler.service"
            subprocess.run(cmd, shell=True)
        except:
            # cmd failed, so profiler service not installed
            self.simple_table_obj. display_dialog_msg(g_vars, 'not available: {}'.format(
                profiler_ctl_file), back_button_req=1)
            g_vars['display_state'] = 'page'
            g_vars['result_cache'] = True
            return
        
        config_file = "/etc/profiler2/config.ini"
      
        dialog_msg = "Unset"
        item_list = []

        # get profiler process status
        # (no check for cached result as need to re-evaluate 
        # on each 1 sec main loop cycle)
        if action == "status":
            
            # check profiler status & return text
            if self.profiler_running():
                item_list = ['Profiler active']
            else:
                item_list = ['Profiler not active']

            self.simple_table_obj.display_simple_table(g_vars, item_list, back_button_req=1,
                                title='Profiler Status')
            g_vars['display_state'] = 'page'
            
            g_vars['result_cache'] = True
            return True

        if action.startswith("start"):
            self.simple_table_obj. display_dialog_msg(g_vars, "Please wait...", back_button_req=0)

            if action == "start":
                # set the config file to use params
                cfg_dict = { "ft_enabled": "True", "he_enabled": "True"}
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_no11r":
                # set the config file to use params
                cfg_dict = { "ft_enabled": "False", "he_enabled": "True"}
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_no11ax":
                # set the config file to use params
                cfg_dict = { "ft_enabled": "True", "he_enabled": "False"}
                self.profiler_ctl_file_update(cfg_dict, config_file)

            else:
                print("Unknown profiler action: {}".format(action))

            if self.profiler_running():
                dialog_msg = 'Already running!'
            else:
                try:
                    cmd = "/bin/systemctl start profiler.service"
                    subprocess.run(cmd, shell=True, timeout=2)
                    dialog_msg = "Started."
                except subprocess.CalledProcessError as proc_exc:
                    dialog_msg = 'Start failed!'
                except subprocess.TimeoutExpired as timeout_exc:
                    dialog_msg = 'Proc timed-out!'
                    
        elif action == "stop":

            self.simple_table_obj. display_dialog_msg(g_vars, "Please wait...", back_button_req=0)

            if not self.profiler_running():
                dialog_msg = 'Already stopped!'
            else:
                try:
                    cmd = "/bin/systemctl stop profiler.service"
                    subprocess.run(cmd, shell=True)
                    dialog_msg = "Stopped"
                except subprocess.CalledProcessError as exc:
                    dialog_msg = 'Stop failed!'
                
        elif action == "purge_reports":
            # call profiler2 with the --clean option

            self.simple_table_obj. display_dialog_msg(g_vars, "Please wait...", back_button_req=0)

            try:
                cmd = "/opt/wlanpi/pipx/bin/profiler --clean --yes"
                subprocess.run(cmd, shell=True)
                dialog_msg = "Reports purged."
            except subprocess.CalledProcessError as exc:
                dialog_msg = "Reports purge error: {}".format(exc)
                print(dialog_msg)
             
        elif action == "purge_files":
            # call profiler2 with the --clean --files option

            self.simple_table_obj. display_dialog_msg(g_vars, "Please wait...", back_button_req=0)

            try:
                cmd = "/opt/wlanpi/pipx/bin/profiler --clean --files --yes"
                subprocess.run(cmd, shell=True)
                dialog_msg = "Files purged."
            except subprocess.CalledProcessError as exc:
                dialog_msg = "Files purge error: {}".format(exc)
                print(dialog_msg)

        # signal that result is cached (stops re-painting screen)
        g_vars['result_cache'] = True

        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
        g_vars['display_state'] = 'page'
        return True


    def profiler_status(self, g_vars):
        self.profiler_ctl(g_vars, action="status")
        return


    def profiler_stop(self, g_vars):
        self.profiler_ctl(g_vars, action="stop")
        return


    def profiler_start(self, g_vars):
        self.profiler_ctl(g_vars, action="start")
        return


    def profiler_start_no11r(self, g_vars):
        self.profiler_ctl(g_vars, action="start_no11r")
        return
    
    def profiler_start_no11ax(self, g_vars):
        self.profiler_ctl(g_vars, action="start_no11ax")
        return

    def profiler_purge_reports(self, g_vars):
        self.profiler_ctl(g_vars, action="purge_reports")
        return

    def profiler_purge_files(self, g_vars):
        self.profiler_ctl(g_vars, action="purge_files")
        return
