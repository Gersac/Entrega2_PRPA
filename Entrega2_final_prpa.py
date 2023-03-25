"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 50
NPED = 10

TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        self.turn = Value('i',0)
        self.npedwaiting=Value('i',0)
        self.pedcross = Condition(self.mutex)
        self.ncar1waiting = Value('i',0)
        self.car1cross = Condition(self.mutex)
        self.ncar2waiting = Value('i',0)
        self.car2cross = Condition(self.mutex)
        self.ncar1crossing=Value('i',0)
        self.ncar2crossing=Value('i',0)
        self.npedcrossing=Value('i',0)
   
    def cross_1(self):
        return (self.turn.value==1 or self.turn.value==-1 )and self.ncar2crossing.value==0 and self.npedcrossing.value==0
    
    def cross_2(self):
        return (self.turn.value==2 or self.turn.value==-1 )and self.ncar1crossing.value==0 and self.npedcrossing.value==0    
    
    def cross_ped(self):
        return (self.turn.value==0 or self.turn.value==-1 )and self.ncar2crossing.value==0 and self.ncar1crossing.value==0     
        
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1 
        if direction==0:
            self.ncar1waiting.value+=1
            self.car1cross.wait_for(self.cross_1)
            self.ncar1waiting.value-=1
            self.ncar1crossing.value+=1
        else:
            self.ncar2waiting.value+=1
            self.car2cross.wait_for(self.cross_2)
            self.ncar2waiting.value-=1
            self.ncar2crossing.value+=1
        self.mutex.release()    

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        if direction==0:
             self.ncar1crossing.value-=1
             if self.npedwaiting.value>=2:
                 self.turn.value=0
             elif self.ncar1waiting.value>=5:
                 self.turn.value=1
             elif self.ncar2waiting.value>=5:
                 self.turn.value=2
             else:
                 self.turn.value=-1
             self.car2cross.notify_all()       
             self.pedcross.notify_all()
        
        else:
             self.ncar2crossing.value-=1
             if self.npedwaiting.value>=2:
                 self.turn.value=0
             elif self.ncar1waiting.value>=5:
                 self.turn.value=1
             elif self.ncar2waiting.value>=5:
                 self.turn.value=2
             else:
                 self.turn.value=-1
             self.car1cross.notify_all()       
             self.pedcross.notify_all()
        self.mutex.release()
    

        
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.npedwaiting.value+=1
        self.pedcross.wait_for(self.cross_ped)
        self.npedwaiting.value-=1
        self.npedcrossing.value+=1
        self.mutex.release()
    
    
    
    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.npedcrossing.value-=1
        if self.npedwaiting.value>=2:
            self.turn.value=0
        elif self.ncar1waiting.value>=5:
            self.turn.value=1
        elif self.ncar2waiting.value>=5:
            self.turn.value=2
        else:
            self.turn.value=-1
        self.car1cross.notify_all()       
        self.car2cross.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    time.sleep(0.5)
    pass

def delay_car_south() -> None:
    time.sleep(0.5)
    pass

def delay_pedestrian() -> None:
    time.sleep(2)
    pass

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()
