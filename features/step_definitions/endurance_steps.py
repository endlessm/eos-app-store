from lettuce import *
from mem_utils import MemUtils
from app_store_manipulator import AppStoreManipulator

@step(u'Given I have the desktop running')
def given_i_have_the_desktop_running(step):
   pass

@step(u'When I reopen the app store (\d+) times')
def when_i_reopen_the_app_store_100_times(step, iterations):
   app_store_manipulator = AppStoreManipulator()
   for i in range(int(iterations)):
      app_store_manipulator.click_through()

@step(u'^Then the memory should not be higher than (\d+)(.*)$')
def then_the_memory_should_not_be_higher_than_850mb(step, max_mem_size, mem_units):
   actual_mem_size = MemUtils().process_mem_size(world.tpid, mem_units) 

   assert actual_mem_size < float(max_mem_size), "Current memory was {0}{2} but we wanted less than {1}{2} ".format(actual_mem_size, max_mem_size, mem_units)

