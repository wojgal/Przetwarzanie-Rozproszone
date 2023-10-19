from mpi4py import MPI
from time import sleep
from colorama import init
import os
from termcolor import colored
import time
import random

os.system('color')
init()

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
color_list = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'black']
color = color_list[rank]

THIEVES_AMOUNT = comm.Get_size()
EQUIPMENT_AMOUNT = 23
LABORATORY_AMOUNT = 10
MIN_CITY_TIME = 1
MAX_CITY_TIME = 10
GOOD_MOOD_PROBABILITY = 0.5
EQUIPMENT_RECOVERY_TIME = 10


# Wypisywanie wykonywanych dzialan
def print_message(message, lamport_clk):
    print(colored(f'[R: {rank}][CLK: {lamport_clk}] {message}', color))



# Poieranie wiadomosci 
def get_messages():
    messages = []

    while True:
        status = MPI.Status()

        if comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG):
            msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
            messages.append((status.Get_source(), msg))
        else:
            return messages
        


# Wysylanie req
def send_request(critical_section_name, lamport_clk):
    msg = f'REQ {critical_section_name} {lamport_clk}'
    comm.Bcast(data=msg, root=rank)


# Wysylanie ack
def send_ack(critical_section_name, lamport_clk, destination_id):
    msg = f'ACK {critical_section_name} {lamport_clk}'
    comm.Send(data=msg, dest=destination_id)


# Ladowanie sie ekwipunku
def charge_equipment():
    SPRZET_AMOUNT -= 1
    print('\t< Ladowanie sprzetu >\t')
    time.sleep(EQUIPMENT_RECOVERY_TIME)


# Krazenie po miescie przez kradzieja
def city_moving():
    while True:
        moving_time = random.randint(MIN_CITY_TIME, MAX_CITY_TIME)
        time.sleep(moving_time)

        if random.random() < GOOD_MOOD_PROBABILITY:
            break



if __name__ == '__main__':
    lamport_clk = 0
    weapon_flag = 'Released'
    laboratory_flag = 'Released'
    equipment_amount = EQUIPMENT_AMOUNT
    laboratory_amount = LABORATORY_AMOUNT

    ack_amount = 0
    weapon_queue = []
    laboratory_queue = []

    # Czytanie wszystkich wiadomosci
    while True:
        messages = get_messages()

        for msg in messages:
            author_id = msg[0]
            msg_type, cs_number, author_clk = msg[1].split()

            print(msg)

            if msg_type == 'RELEASE':
                pass

            elif msg_type == 'ACK':
                pass

            elif msg_type == 'REQ':
                pass

    # Kradziej chce pozyskac bron
    if weapon_flag == 'Released':
        send_request(1, lamport_clk)
        print_message('chce wejsc do sekcji WEAPON', lamport_clk)

        ack_amount = 0
        weapon_flag = 'Wanted'

    # Kradziej pozyskuje bron
    elif weapon_flag == 'Wanted':
        if ack_amount >= THIEVES_AMOUNT and equipment_amount > 0:
            lamport_clk += 1
            print_message('wchodzi do sekcji krytycznej WEAPON', lamport_clk)

            equipment_amount -= 1
            ack_amount = 0
            weapon_flag = 'Held'

    # Kradziej szuka humoru
    if weapon_flag == 'Held' and laboratory_flag == 'Released':
        print_message('krazy po miescie', lamport_clk)
        city_moving()

        send_request(2, lamport_clk)
        
        ack_amount = 0
        laboratory_flag = 'Wanted'

    # Kradziej chce dostac sie do laboratorium
    if weapon_flag == 'Held' and laboratory_flag == 'Wanted':
        if ack_amount >= THIEVES_AMOUNT and laboratory_amount > 0:

            lamport_clk += 1
            print_message('wchodzi do sekcji krytycznej LABORATORY', lamport_clk)
            print('\t< WYPRODUKOWANO GUME >\t')
            lamport_clk += 1
            print_message('wychodzi z sekcji krytycznej LABORATORY', lamport_clk)

            ack_amount = 0




    
                
            






