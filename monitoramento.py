from psutil import (
	virtual_memory, 
	swap_memory,
	cpu_percent,
	sensors_temperatures,
	disk_io_counters,
	disk_partitions,
	disk_usage,
	net_if_addrs,
	net_io_counters,
	users,
	boot_time,
	pids,
	process_iter,
	sensors_battery,
	) 
from dashing import HSplit, VSplit,VGauge, HGauge, Text
from time import sleep
from datetime import datetime
from cpuinfo import get_cpu_info
from GPUtil import getAvailable
import platform
import pandas as pd

def bytes_to_gb(value):
	return value / 1024 / 1024 / 1024

ui = HSplit( # ui
	VSplit(
		Text(' ',
		border_color = 1,
		title = 'Info Computador'),

		Text(' ',
		border_color = 2,
		title = 'Rede'),

		Text(
			' ',
			title = 'Disco',
			border_color = 3),
	),
	
	VSplit(# ui.items[1]
		HGauge(title='CPU %'),
		HGauge(title='cpu_0 %'),
		HGauge(title='cpu_1 %'),
		HGauge(title='cpu_2 %'),
		HGauge(title='cpu_3 %'),
		HGauge(title='cpu_temp %'),
		HGauge(title='acpitz_temp %'),


		title = 'CPU',
		border_color=4,
			
	),
	VSplit( # ui.items[2].items[0]
		HSplit( # ui.items[2]
		VGauge(title='RAM'), # ui.items[2].items[0]
		VGauge(title='SWAP'),# ui.items[2].items[1]
		title='Memória',
		border_color = 5
		),
			
		Text( # ui.items[2].items[1]
			' ',
			title = 'Processos',
			border_color = 6),
		),
		
)
#criando DF's
#df_cpu
n_colunas = len(cpu_percent(percpu=True))
colunas = ['CPU']
n=-1
for _ in range(n_colunas):
	n+=1
	colunas.append(f'cpu_{n}')

df_cores = pd.DataFrame(columns=['Geral',
								'cpu_0',
								'cpu_1',
								'cpu_2',
								'cpu_3',
								'Memoria',
								'SWAP',								
								'Temperatura',
								'Temperatura acpitz',
								'Battery',
								'Date'])
df_cores.to_csv('df_info.csv', index=False)



while True:
	# Info Computador
	info_tui = ui.items[0].items[0]
	cpu = get_cpu_info()['brand_raw']
	gpu = getAvailable()
	memory = virtual_memory().total
	storage = disk_usage('/')
	system = platform.system() + platform.release()	
	op = "-".join(platform.dist())

	boot = datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")

	info_tui.text = f'\033[mUsuário: {users()[0].name}\033[m\n'
	info_tui.text += f'\033[mBoot: {boot}\033[m\n\n'


	info_tui.text += f'\033[mProcessador: {cpu}\033[m\n'
	info_tui.text += f'\033[mGPU: {gpu}\033[m\n'
	info_tui.text += f'\033[mMemória: {bytes_to_gb(memory):.2f}GB\033[m\n'
	info_tui.text += f'\033[mArmazenamento: {bytes_to_gb(storage.total):.2f}GB\033[m\n'

	info_tui.text += f'\033[mKernel: {system}\033[m\n'
	info_tui.text += f'\033[mSistema operacional: {op}\033[m\n'

	battery = sensors_battery()
	if battery:
		battery_charge = battery.percent
		info_tui.text += "charge = %s%%, time left = %s" % (battery_charge, secs2hours(battery.secsleft))
	else:
		info_tui.text += f'\033[mSem bateria identificada\033[m\n'
		battery_charge = '-'

	# Processos
	proc_tui = ui.items[2].items[1]
	proc_tui.text += f'\nProcessos: {len(pids())}'

	p_list = []
	for proc in process_iter():
		proc_info = proc.as_dict(attrs=['name', 'cpu_percent'])

		if proc_info['cpu_percent'] > 0:
			p_list.append(proc_info)

	ordenados = sorted(p_list,key=lambda p: p['cpu_percent'],reverse=True)[:20]

	proc_tui.text = f"\033[m{'Nome':<30}CPU(%)\033[m"
	for proc in ordenados:
		proc_tui.text += f"\n\033[m{proc['name']:<30} {proc['cpu_percent']}\033[m"

	# # Memória
	mem_tui = ui.items[2].items[0]
	# Ram
	ram_tui = mem_tui.items[0]
	ram_tui.value = virtual_memory().percent
	ram_tui.title = f'RAM {ram_tui.value} %'

	# SWAP
	swap_tui = mem_tui.items[1]
	swap_tui.value = swap_memory().percent
	swap_tui.title = f'SWAP {swap_tui.value} %'

	#CPU
	cpu_tui = ui.items[1]
	#CPU%
	cpu_percent_tui = cpu_tui.items[0]
	ps_cpu_percent = cpu_percent()
	cpu_percent_tui.value = ps_cpu_percent
	cpu_percent_tui.title = f'CPU {ps_cpu_percent}%'

	# porcentagem dos cores
	cores_tui = cpu_tui.items[1:5]
	ps_cpu_percent = cpu_percent(percpu=True)

	for i, (core, value) in enumerate(zip(cores_tui, ps_cpu_percent)):
		core.value = value
		core.title = f'cpu_{i} {value}%'


	#CPU Temperatura
	cpu_temp_tui = cpu_tui.items[5]
	ps_cpu_temp = sensors_temperatures()['coretemp'][0]
	cpu_temp_tui.value = ps_cpu_temp.current
	cpu_temp_tui.title = f'CPU Temp {ps_cpu_temp.current}C'

	#acpitz Temperatura
	acpitz_temp_tui = cpu_tui.items[6]
	ps_acpitz_temp = sensors_temperatures()['acpitz'][0]
	acpitz_temp_tui.value = ps_acpitz_temp.current
	acpitz_temp_tui.title = f'acpitz Temp {ps_acpitz_temp.current}C'

	#Disco
	disk_tui =  ui.items[0].items[2]
	partitions = disk_partitions()
	counters = disk_io_counters(perdisk=True)

	disk_tui.text = '\033[mTotal: {:.0f}Gb Usado: {:.0f}Gb Livre: {:.0f}Gb Uso: {:.0f}%\033[m\n\n'.format(
		bytes_to_gb(storage.total),
		bytes_to_gb(storage.used),
		bytes_to_gb(storage.free),
		storage.percent
		)
	disk_tui.text += f"\033[m{'Partição':<15}{'Uso(%)':<10}{'Lido(Mb)':10}{'Escrito(Mb)'}\033[m\n"
	d_list = []
	for partition in partitions:
		partition_name_counter = partition.device.split('/')[-1]

		if partition_name_counter != 'ubuntu--vg-root':
			disk_bytes = counters[partition_name_counter]
			line = {'device': partition.device,
			'disk_usage': disk_usage(partition.mountpoint).percent,
			'read_bytes': bytes_to_gb(disk_bytes.read_bytes),
			'write_bytes': bytes_to_gb(disk_bytes.write_bytes)}

			d_list.append(line)


	ordenados = sorted(d_list,key=lambda p: p['read_bytes'],reverse=True)[:10]

	for p in ordenados:
		disk_tui.text += '\033[m{:<15} {:<10} {:<6.3f}{:10.3f}\n\033[m'.format(
			p['device'],
			p['disk_usage'],
			p['read_bytes']*1024,
			p['write_bytes']*1024)

	# Rede
	network_tui = ui.items[0].items[1]
	addrs_v4 = net_if_addrs()['eno1'][0]
	addrs_v6 = net_if_addrs()['eno1'][1]

	network_tui.text = f'\033[mIPV4: {addrs_v4.address}\033[m\n'
	network_tui.text += f'\033[mMASK IPV4: {addrs_v4.netmask}\033[m\n'
	network_tui.text += f'\033[mIPV6: {addrs_v6.address}\033[m\n'
	network_tui.text += f'\033[mMASK IPV6: {addrs_v6.netmask}\033[m\n\n'

	network_tui.text += f'\033[mGb Enviado: {bytes_to_gb(net_io_counters().bytes_sent):.2f}GB\033[m\n'
	network_tui.text += f'\033[mGb Recebido: {bytes_to_gb(net_io_counters().bytes_recv):.2f}GB\033[m\n'
	network_tui.text += f'\033[mPacotes enviados: {net_io_counters().packets_sent}\033[m\n'
	network_tui.text += f'\033[mPacotes recebidos: {net_io_counters().packets_recv}\033[m\n'	
	network_tui.text += f'\033[mErros ao enviar: {net_io_counters().errin}\033[m\n'
	network_tui.text += f'\033[mErros ao receber: {net_io_counters().errout}\033[m\n'
	network_tui.text += f'\033[mTotal de pacotes recebidos descartados: {net_io_counters().dropin}\033[m\n'
	network_tui.text += f'\033[mTotal de pacotes de saída descartados: {net_io_counters().dropout}\033[m\n'

	#df_cpu
	n_colunas = len(cpu_percent(percpu=True))
	colunas = ['CPU']
	n=-1
	for _ in range(n_colunas):
		n+=1
		colunas.append(f'cpu_{n}')

	df_cores = pd.DataFrame(columns=['Geral',
								'cpu_0',
								'cpu_1',
								'cpu_2',
								'cpu_3',
								'Memoria',
								'SWAP',								
								'Temperatura',
								'Temperatura acpitz',
								'Battery',
								'Date'])
	date_time = datetime.now().strftime("%A %d %B %y %I:%M")

	cores_data = [[cpu_percent(),
				ps_cpu_percent[0],
				ps_cpu_percent[1],
				ps_cpu_percent[2],
				ps_cpu_percent[3],
				ram_tui.value,
				swap_tui.value,
				cpu_temp_tui.value,
				acpitz_temp_tui.value,
				battery_charge,
				date_time
				]]

	df_cores=pd.DataFrame(cores_data)

	df_cores.to_csv('df_info.csv', index=False, mode='a', header=False)


	try:
		ui.display()
		sleep(.5)
	except KeyboardInterupt:
		break
