I used python 3.7.3

Results are as follows.
  --result#1
  	# run the client1.py program and the server1.py program on different machines.
	D:\_Work\Github\352-RDP-v1>python client1.py -d 192.168.6.219 -f sendfile.pdf -u 9999 -v 8888
	client1: sent 52438 bytes in 0.022792 seconds, 2.194137 MB/s

  --result#2
  	# run the client1.py program and the server1.py program on different machines.
	D:\_Work\Github\352-RDP-v1>python client1.py -d 192.168.6.219 -f python.zip -u 9999 -v 8888
	client1: sent 123509523 bytes in 59.117845 seconds, 1.992425 MB/s

  --result#3
  	# run the client1.py program and the server1.py program on same machine.
  	D:\_Work\Github\352-RDP-v1>python server1.py -f savedfile.pdf -u 8888 -v 9999
	server1: received 143003 bytes in 0.015511 seconds, 8.792076 MB/s
	D:\_Work\Github\352-RDP-v1>python client1.py -d localhost -f cs352.pdf -u 9999 -v 8888
	client1: sent 143003 bytes in 0.015485 seconds, 8.807179 MB/s

