from mpi4py import MPI
from time import sleep
from colorama import init
import os
from termcolor import colored
import time
import random
import threading

os.system('color')
init()

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
color_list = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'black']
color = color_list[rank]

THIEVES_AMOUNT = comm.Get_size()
EQUIPMENT_AMOUNT = 1
LABORATORY_AMOUNT = 1
MIN_CITY_TIME = 1
MAX_CITY_TIME = 10
GOOD_MOOD_PROBABILITY = 0.5
EQUIPMENT_RECOVERY_TIME = 10


# Wypisywanie wykonywanych dzialan
def print_message(message, lamport_clk):
    print(colored(f'[R:{rank}][CLK:{lamport_clk}] {message}', color))



# Poieranie wiadomosci 
def get_messages():
    messages = []

    while True:
        status = MPI.Status()

        if comm.Iprobe(source=MPI.ANY_SOURCE, status=status):
            msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
            messages.append((status.Get_source(), msg))
        else:
            return messages
        

# Broadcast do wszystkich
def bcast(message, rank):
    for dest_id in range(4):
        if dest_id == rank:
            continue
        comm.send(message, dest=dest_id)



# Wysylanie req
def send_request(critical_section_name, lamport_clk):
    msg = f'REQ {critical_section_name} {lamport_clk}'
    bcast(msg, rank)


# Wysylanie ack
def send_ack(critical_section_name, lamport_clk, destination_id):
    msg = f'ACK {critical_section_name} {lamport_clk}'
    comm.send(msg, dest=destination_id)
    


# Wysyłanie realease
def send_release(critical_section_name, lamport_clk):
    msg = f'REL {critical_section_name} {lamport_clk}'
    bcast(msg, rank)


# Ladowanie sie ekwipunku
def charge_equipment(lamport_clk):
    print('\t< Ladowanie sprzetu >\t\n')
    time.sleep(EQUIPMENT_RECOVERY_TIME)
    send_release('WEAPON', lamport_clk)
    print('\t< Sprzed naladowany >\t\n')



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
    weapon_amount = EQUIPMENT_AMOUNT
    laboratory_amount = LABORATORY_AMOUNT

    ack_amount = 0
    weapon_queue = []
    laboratory_queue = []

    # Czytanie wszystkich wiadomosci
    while True:
        messages = get_messages()

        for msg in messages:
            author_rank = msg[0]
            msg_type, cs_name, author_clk = msg[1].split()
            author_clk = int(author_clk)

            if msg_type == 'REL':
                if cs_name == 'WEAPON':
                    weapon_amount += 1
                    #print_message('zwalnia WEAPON', lamport_clk)

                elif cs_name == 'LABORATORY':
                    laboratory_amount += 1
                    #print_message('zwalnia LABORATORY', lamport_clk)
                

            elif msg_type == 'ACK':
                if weapon_flag == 'Wanted' or laboratory_flag == 'Wanted':
                    ack_amount += 1
                    print_message(f'Otrzymano potwierdzenie od {author_rank}', lamport_clk)

            #zajebane 1 do 1, chuj wie czy dziala
            elif msg_type == 'REQ':
                if cs_name == 'WEAPON':
                    if weapon_flag == 'Held' or lamport_clk < author_clk or (lamport_clk == author_clk and rank < author_rank):
                        weapon_queue.append(msg)

                    else:
                        send_ack('WEAPON', lamport_clk, author_rank)
                        weapon_amount -= 1
                        lamport_clk += 1
                        print_message(f'Wyslanie ack WEAPON do {author_rank}', lamport_clk)

                elif cs_name == 'LABORATORY':
                    if laboratory_flag == 'Held' or lamport_clk < author_clk or (lamport_clk == author_clk and rank < author_rank):
                        laboratory_queue.append(msg)

                    else:
                        send_ack('LABORATORY', lamport_clk, author_rank)
                        lamport_clk += 1
                        print_message(f'Wyslanie ack LABORATORY do {author_rank}', lamport_clk)

        #print_message(ack_amount, lamport_clk)
        # Kradziej chce pozyskac bron
        if weapon_flag == 'Released':
            send_request('WEAPON', lamport_clk)
            weapon_queue.append((rank, f'ACK WEAPON {lamport_clk}'))
            print_message('Chce wejsc do sekcji WEAPON', lamport_clk)

            ack_amount = 1
            weapon_flag = 'Wanted'
        
        # Kradziej pozyskuje bron
        elif weapon_flag == 'Wanted':
            if ack_amount >= THIEVES_AMOUNT - weapon_amount and weapon_amount > 0:
                lamport_clk += 1
                print_message('Wchodze do sekcji krytycznej WEAPON', lamport_clk)

                weapon_amount -= 1
                ack_amount = 0
                weapon_flag = 'Held'

        # Kradziej szuka humoru
        elif weapon_flag == 'Held' and laboratory_flag == 'Released':
            print_message('Kraze po miescie', lamport_clk)
            city_moving()

            send_request('LABORATORY', lamport_clk)
            laboratory_queue.append((rank, f'ACK WEAPON {lamport_clk}'))
            
            ack_amount = 1
            laboratory_flag = 'Wanted'

        # Kradziej chce dostac sie do laboratorium
        elif weapon_flag == 'Held' and laboratory_flag == 'Wanted':
            if ack_amount >= THIEVES_AMOUNT - laboratory_amount and laboratory_amount > 0:

                lamport_clk += 1
                print_message('Wchodzi do sekcji krytycznej LABORATORY', lamport_clk)
                print('\t< WYPRODUKOWANO GUME >\t')
                lamport_clk += 1
                print_message('Wychodzi z sekcji krytycznej LABORATORY', lamport_clk)

                ack_amount = 0

                #zajebane 1 do 1 moze nie dzialac
                for msg in laboratory_queue:
                    author_rank = msg[0]
                    msg_type, cs_name, author_clk = msg[1].split()
                    author_clk = int(author_clk)

                    if author_rank == rank:
                        continue

                    send_ack('LABORATORY', lamport_clk, author_rank)

                    if cs_name == 'WEAPON':
                        weapon_amount -= 1
                    
                    lamport_clk = max(lamport_clk, author_clk) + 1
                    print_message('jakis msg 6', lamport_clk)

                weapon_queue.clear()
                laboratory_queue.clear()

                chare_thread = threading.Thread(target=lambda: charge_equipment(lamport_clk))
                chare_thread.start()

                lamport_clk += 1
                print_message('jakis msg 7', lamport_clk)

                weapon_flag = 'Released'
                laboratory_flag = 'Released'



