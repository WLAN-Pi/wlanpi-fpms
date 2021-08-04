import subprocess
import os.path
import socket

from modules.pages.simpletable import * 

class CloudUtils(object):

    def __init__(self, g_vars):
       
        # create simple table object to show dialog & results on display 
        self.simple_table_obj = SimpleTable(g_vars)


    def test_mist_cloud(self, g_vars):
        '''
        Perform a series of connectivity tests to see if Mist cloud available:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3. Can we resolve address  ep-terminator.mistsys.net
        4. Can get get a http 200 response to https://ep-terminator.mistsys.net/about

        '''
        
        # ignore any more key presses as this could cause us issues
        g_vars['disable_keys'] = True
        
        # Has speedtest been run already?
        if g_vars['speedtest_status'] == False:
        
            # record test success/fail
            test_fail = False

            # paint our empty table
            item_list = ['...Testing', '', '', '']
            self.simple_table_obj.display_simple_table(g_vars, item_list, back_button_req=0, title='--Mist Cloud--')

            # Is eth0 up?
            cmd = "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'"
            result = subprocess.check_output(cmd, shell=True).decode().strip()

            if result == 'yes':
                item_list[0] = "Eth port up:    YES"
            elif result == 'no':
                item_list[0] = "Eth port up:     NO"
                test_fail = True
            else:
                item_list[0] = "Eth port up:unknown"
                test_fail = True
            
            # we're done if test failed
            if not test_fail:
                # Have we got an IP address?
                cmd = "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
                result = subprocess.check_output(cmd, shell=True).decode()

                if result:
                    item_list[1] = "IP: {:>16}".format(result)
                else:
                    item_list[1] = "IP:            None"
                    test_fail = True
            
            if not test_fail:
                # Can we resolve address ep-terminator.mistsys.net?
                try:
                    socket.gethostbyname("ep-terminator.mistsys.net")
                    item_list[2] = "DNS:             OK"
                except:
                    test_fail = True
                    item_list[2] = "DNS:           FAIL"

            if not test_fail:
                # Can we get an http 200 from https://ep-terminator.mistsys.net/about ?
                cmd = 'curl -k -s -o /dev/null -w "%{http_code}" https://ep-terminator.mistsys.net/about'
                result = subprocess.check_output(cmd, shell=True).decode()

                if result == '200':
                    item_list[3] = "HTTP:            OK"
                else:
                    item_list[3] = "HTTP:          FAIL"
                    test_fail = True

            # show results
            self.simple_table_obj.display_simple_table(g_vars, item_list, back_button_req=1, title='--Mist Cloud--')

            # set flag to prevent constant refresh of screen
            g_vars['speedtest_status'] = True
    
        # re-enable front panel keys
        g_vars['disable_keys'] = False


