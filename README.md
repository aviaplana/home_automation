#Home automation
...Work in progress...
##Packet structures
###Serial communication
####Main node to broker
Field | \B | Payload size | Type | ID | Payload | \E
------|:--:|:------------:|:----:|:--:|:-------:|:--:
**Bytes** | 2 | 1 | 1 | 1 | ? | 2

 + **\B** : Initial sequence.
 + **Payload size** : Length of the payload, in Bytes.
 + **Type** : Payload type.
 + **ID** : ID of the node that is sending packet.
 + **Payload** : The information to send.
 + **\E** : Ending sequence.

####Broker to main node
Field | \B | Type | ID | Payload | \E
------|:--:|:----:|:--:|:-------:|:--:
**Bytes** | 2 | 1 | 1 | ? | 2

 + **\B** : Initial sequence.
 + **Type** : Payload type.
 + **ID** : ID of the node that will receive the packet.
 + **Payload** : The information to send.
 + **\E** : Ending sequence.

###Radio communication
Field | Type | ID | Payload
------|:----:|:--:|:-------:
**Bytes** | 1 | 1 | ? 

 + **Type** : Payload type.
 + **ID** : ID of the node that will receive the packet.
 + **Payload** : The information to send.

---

##Packet types
Type          |   Code
--------------|:-------:
Ping          |  0
Confirmation  |  1
Initialization request    |  2
Initialization response    |  3
Initialization info request    |  4
Initialization info response    |  5
Initialization reset    |  6
Add node | 10
Delete node | 11
Delete list | 12
RGB          |  20


---

##Payloads
###RGB
Used to interact with the RGB led strip.

Field     | R | G | B | Is on | Reserved | Instruction | Blink freq. | Fade dur.
----------|:-:|:-:|:-:|:-----:|:--------:|:-----------:|:-----------:|:--------:
          |   |   |   | 1 bit |  1 bit   |   6 bits    |             | 
**Bytes** | 1 | 1 | 1 |       |     1    |             |      2      |     2

 + **R** : Red value. From 0 to 255.
 + **G** : Green value. From 0 to 255.
 + **B** : Blue value. From 0 to 255.
 + **Is on** : 1 if the light is on, 0 if it's off
 + **Reserved** : Reserved for future use
 + **Blink frequency** : Blink frequency in milliseconds. From 0 to 65,535.
 + **Fade duration** : Fade duration in milliseconds. From 0 to 65,535.
 + **Instruction** : See the table below

Instruction        | Code
-------------------|:------:
Change all values  | 0
Set default values | 1
On                 | 2
Off                | 3
Toggle             | 4
Change color       | 10
Change blink       | 11
Get current values | 20
Get default values | 21
Error              | 63

###INIT REQUEST
Requests initialization information to the broker. Sent by the nodes.

Field | Hash | Type
------|:----:|:----:
**Bytes** | 2 | 1  

+ **Hash** : Random number used to identify the node that sent the packet.
+ **Type** : Node type (RGB, temperature sensor...).

###INIT RESPONSE
Requests initialization information to the broker. Sent by the nodes.

Field | Hash | PIPE
------|:----:|:----:
**Bytes** | 2 | 1  

+ **Hash** : Hash number specified in the INIT REQUEST packet. 
+ **Pipe** : Pipe assigned to the node.

###INIT INFO RESPONSE PACKET
Sends the actual initialization information of the node. Sent when a INIT INFO REQUEST packet is received.

Field | Pipe | Type
------|:----:|:----:
**Bytes** | 1 | 1  

+ **Pipe** : Pipe assigned to the node.
+ **Type** : Node type (RGB, temperature sensor...).

###DELETE NODE
This packet is sent by the broker to the main node through serial communication.  Deletes a node from the node list.

Field | ID
------|:--:
**Bytes** | 1   

+ **ID** : ID of the node to delete.

###ADD NODE
This packet is sent by the broker to the main node through serial communication.  Adds a node to the node list.

Field | ID | Pipe
------|:----:|:----:
**Bytes** | 1 | 1  

+ **Pipe** : Piipe assigned to the node. 
+ **ID** : ID number assigned to the node.

