#!/usr/bin/env python
'''battery demo command'''

from pymavlink import mavutil

from MAVProxy.modules.lib import mp_module

from MAVProxy.modules.mavproxy_battery_demo.formula_agent import run_agent_executor, run_agent_executor_repair

import re, os

from pythonnet import load
load("coreclr")
import clr

formula_dll = os.environ.get("FORMULA_DLL_PATH", False)

if formula_dll != False:
    clr.AddReference(formula_dll)
else:
    raise ValueError('FORMULA_DLL_PATH envionment variable not set.')

from Microsoft.Formula.CommandLine import CommandInterface, CommandLineProgram
from System.IO import StringWriter
from System import Console 

class BatteryDemoModule(mp_module.MPModule):
    def __init__(self, mpstate):
        super(BatteryDemoModule, self).__init__(mpstate, "battery_demo", "battery demo command", public=True)
        self.add_command('batdemo', self.cmd_bat_demo, "run battery demo")
        self.arm_module = self.module('arm')
        self.mode_module = self.module('mode')
        self.wp_module = self.module('wp')
        self.cmdlong_module = self.module('cmdlong')
        self.armed = False
        self.battery_cap = 300000.0
        self.rate = 116.67
        self.consumed_cap = 0.0
        self.battery_period = mavutil.periodic_event(1)
        self.print_period = mavutil.periodic_event(0.25)
        self.explain_prompt = "Given the following Formula DSL program modeling a physical drone, explain what the invalidBatteryPartialModel partial model is modeling. Give a detailed list of solutions, such as reducing payload weights, that can be made to the partial model invalidBatteryPartialModel to fix the partial model so that the drone has a high enough battery capacity to fly."
        self.repair_prompt = "Repair the invalidBatteryPartialModel by reducing the payload1 and body component weights so that the sum of the missionConsumptions will be below the batteryCapacity. Do not shorten or comment that the code remains the same in the edited code."
        self.save_file = "./data/IBC_Repaired.4ml"
        self.sw = StringWriter()
        Console.SetOut(self.sw)
        Console.SetError(self.sw)

        sink = CommandLineProgram.ConsoleSink()
        chooser = CommandLineProgram.ConsoleChooser()
        self.ci = CommandInterface(sink, chooser)

        if not self.ci.DoCommand('wait on'):
            print("Wait command failed.")
            return

    def cmd_bat_demo(self, args):
        if len(args) != 1:
             return
       
        if not self.ci.DoCommand('unload *'):
            print("Solve command failed.")
            return
        
        if not self.ci.DoCommand('tunload *'):
            print("Solve command failed.")
            return
        
        self.sw.GetStringBuilder().Clear()
        
        file = ""
        code = ""
        if args[0] == 'repair':
            file = './data/InvalidBatteryChecker.4ml'  
            code = ""
            with open(file, 'r') as f:
                code = f.read()
            output = "Model is not solvable."
            run_agent_executor_repair(code, output, self.repair_prompt)
            file = "./data/valid.4ml"
        elif args[0] == 'invalid':
            file = './data/InvalidBatteryChecker.4ml'  
            with open(file, 'r') as f:
                code = f.read()

        if not self.ci.DoCommand('load ' + file):
            print("Load command failed.")
            return
        
        output = self.sw.ToString()
        self.sw.GetStringBuilder().Clear()
        print(output)
        
        mission = ""
        if args[0] == 'repair':
            mission = './data/ValidMission.txt'
            if not self.ci.DoCommand('solve invalidBatteryPartialModel 1 BatteryChecker.conforms'):
                print("Solve command failed.")
                return
        elif args[0] == 'invalid':
            if not self.ci.DoCommand('solve invalidBatteryPartialModel 1 BatteryChecker.conforms'):
                print("Solve command failed.")
                return

        output = self.sw.ToString()
        self.sw.GetStringBuilder().Clear()
        print(output)

        if not self.ci.DoCommand('extract 0 0 0'):
                print("Extract command failed.")
                return
            
        output = self.sw.ToString()
        self.sw.GetStringBuilder().Clear()

        if re.search("Model\s+not\s+solvable\.", output):
            print("Model returned not solvable. Running GPT explaination.")
            run_agent_executor(code, output, self.explain_prompt)
            return
        elif re.search("Solution\s+number", output):
            match = re.search("batteryCapacity\((\d+)\/(\d+)\)", output)
            if match != None:
                top = match.group(1)
                bot = match.group(2)

                calc = float(top)/float(bot)

                per = (calc/self.battery_cap)*100.0

                print("Calculated battery capacity: {:.2f} Joules".format(calc))
                print("Drone battery capacity: {:.2f} Joules".format(self.battery_cap))

                if calc < self.battery_cap:
                    print("Battery capacity sufficient. Loading waypoints...")
                    self.wp_module.cmd_wp(['load', mission])
                    self.wp_module.wp_add_landing()
                else:
                    print("Battery capacity exceeded. Stopping run.")
                    return
                
            match = re.search("rate\((\d+)\/(\d+)\)", output)
            if match != None:
                top = match.group(1)
                bot = match.group(2)

                calc = float(top)/float(bot)
                print("Rate: {:.2f} Joules".format(calc))

    def update_capacity(self):
        self.consumed_cap += self.rate*0.4497
    
    def print_capacity(self):
        print("Consumed battery capacity: {:.2f} Joules".format(self.consumed_cap))

    def mavlink_packet(self, m):
        '''handle a mavlink packet'''
        if self.master.flightmode == 'AUTO' and self.battery_period.trigger():
            self.update_capacity()
        if  self.master.flightmode == 'AUTO' and self.print_period.trigger():
            self.print_capacity()

def init(mpstate):
    '''initialise module'''
    return BatteryDemoModule(mpstate)
