package clients.java;
import org.zeromq.ZMQ;
import org.zeromq.SocketType;
import org.apache.zookeeper.*;
import org.apache.zookeeper.data.*;
import java.util.*;
import OpWire.*;

public class Client implements org.apache.zookeeper.Watcher {
	public static final int CLIENT_PORT = 2181;
	public static final int QUORUM_PORT = 2888;
	public static final int ELECTION_PORT = 3888;
	public static final int SESSION_TIMEOUT = 100000000; //Time to session timeout in ms
	public static final Client CLIENT = new Client();

	final java.util.concurrent.CountDownLatch connectedSignal = new java.util.concurrent.CountDownLatch(1);

	public void process(org.apache.zookeeper.WatchedEvent we){ 
		try{
			if (we.getState() == Watcher.Event.KeeperState.SyncConnected) {
				connectedSignal.countDown();
				java.util.concurrent.TimeUnit.SECONDS.sleep(2);
			}
		} catch(Exception e) {
			if (we.getState() == Watcher.Event.KeeperState.SyncConnected) {
				connectedSignal.countDown();
			}
		}
	}
	
	public Client(){ ; }

	public OpWire.Message.Operation receiveOp(ZMQ.Socket socket) throws Exception{
		byte[] payload = socket.recv(0);
		OpWire.Message.Operation op = OpWire.Message.Operation.parseFrom(payload);
//		System.out.println("CLIENT: Recieved OP.");
		return op;
	}


	public OpWire.Message.Response put(ZooKeeper client, OpWire.Message.Operation opr, int clientId, String quorum) throws Exception{
		String err = "None";
		String path = "/" + opr.getPut().getKey();
		String data = opr.getPut().getValue().toString();
		long start = 0L, start2 = 0L;
		long stop = 0L, stop2 = 0L;
		int tries = 0;
//		System.out.println("CLIENT: About to send PUT request.");
		do {
			tries += 1;
			org.apache.zookeeper.ZooKeeper.States state = client.getState();
			switch(state){
				case ASSOCIATING:
				case CONNECTING:
				case CONNECTEDREADONLY:
					while(client.getState() != ZooKeeper.States.CONNECTED){ 
						;
					}
				case CONNECTED:
					try{
						start = System.currentTimeMillis();
						start2 = System.nanoTime();
						client.setData(path, data.getBytes(), -1);
						stop2 = System.nanoTime();
						stop = System.currentTimeMillis();
					} catch(KeeperException.NoNodeException n) {
						start = System.currentTimeMillis();
						start2 = System.nanoTime();
						try{
							client.create(path, data.getBytes(), ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);
						} catch(Exception e) {
							err = "Caught Exception: " + e.getMessage();
						}
						stop2 = System.nanoTime();
						stop = System.currentTimeMillis();
					} catch(Exception k) {
						err = "Caught Exception: " + k.getMessage();
					}
					break;
				default:
					start = System.currentTimeMillis();
					start2 = System.nanoTime();
					stop2 = System.nanoTime();
					stop = System.currentTimeMillis();
					err = "Bad system state: " + state;
					break;
			}
			
			if(!err.equals("None")){
				System.out.println("CLIENT: Non-None Error: " + err);
				System.out.println("CLIENT: Making new ZooKeeper.");
				client = new ZooKeeper(quorum, SESSION_TIMEOUT, new Client());
				err = "Failed: " + tries + " tries.";
			}

		} while (!err.equals("None") && tries < 1);
//		System.out.println("CLIENT: PUT successfully.");
		double duration = (stop2 - start2 + 0.0) / 1E9; // Duration in seconds.
		OpWire.Message.Response resp = OpWire.Message.Response.newBuilder()
							     .setResponseTime(duration)
							     .setErr(err)
							     .setClientStart(start / 1E3)
							     .setQueueStart(opr.getPut().getStart())
							     .setEnd(stop / 1E3)
							     .setClientid(clientId)
							     .setOptype("Write")
							     .setTarget("N/A")
							     .build();
		return resp;
	}

	public OpWire.Message.Response get(ZooKeeper client, OpWire.Message.Operation opr, int clientId, String quorum) throws Exception{
		String err = "None";
		String path = "/" + opr.getGet().getKey();
		long start, start2, stop, stop2 = 0L;
		int tries = 0;
		do{
		tries += 1;
		org.apache.zookeeper.ZooKeeper.States state = client.getState();
		switch(state){
			case ASSOCIATING:
			case CONNECTING:
				while(client.getState() != ZooKeeper.States.CONNECTED
				   && client.getState() != ZooKeeper.States.CONNECTEDREADONLY){ ; }
			case CONNECTEDREADONLY:
			case CONNECTED:
				start = System.currentTimeMillis();
				start2 = System.nanoTime();
				
				try{
					client.getData(path, false, client.exists(path, false));
				} catch(Exception e) {
					err = "Caught Exception: " + e.getMessage();
				}
				stop2 = System.nanoTime();
				stop = System.currentTimeMillis();
				break;
			default:
				start = System.currentTimeMillis();
				start2 = System.nanoTime();
				stop2 = System.nanoTime();
				stop = System.currentTimeMillis();
				err = "Bad system state: " + state;
				break;
		}

		if(!err.equals("None")){
			err = "Failed: " + tries + " times.";
			client = new ZooKeeper(quorum, SESSION_TIMEOUT, new Client());
		}

		} while(!err.equals("None") && tries < 1);
		double duration = (stop2 - start2 + 0.0) / 1E9; // Duration in seconds.
		OpWire.Message.Response resp = OpWire.Message.Response.newBuilder()
							     .setResponseTime(duration)
							     .setErr(err)
							     .setClientStart(start / 1E3)
							     .setQueueStart(opr.getGet().getStart())
							     .setEnd(stop / 1E3)
							     .setClientid(clientId)
							     .setOptype("Read")
							     .setTarget("N/A")
							     .build();
		return resp;
	}


	public static void main(String[] args) throws Exception {

		Client mainClient = new Client();
		String[] endpoints = args[0].split(",");
		int clientId = Integer.parseInt(args[1]);
		String address = "127.0.0.1:10000"; // args[2]; // for now, resort to magic constants



		ZMQ.Context context = ZMQ.context(1);			// Creates a context with 1 IOThread.
		ZMQ.Socket socket = context.socket(SocketType.REQ);
		
		String quorum = String.join(":" + CLIENT_PORT + ",", endpoints) + ":" + CLIENT_PORT;
//		System.out.println("CLIENT: Creating first ZK.");
		ZooKeeper cli = new ZooKeeper(quorum, SESSION_TIMEOUT, new Client());
//		System.out.println("CLIENT: Connected to first ZK.");
	
		String binding;
		boolean quits = false;
		OpWire.Message.Response resp = null;
		byte[] payload;
		
		socket.connect("tcp://" + address);
		
		socket.send("", 0);
		while(!quits){
			OpWire.Message.Operation opr = mainClient.receiveOp(socket);
			System.out.println("Client: Sending op.");
			switch(opr.getOpTypeCase().getNumber()){
				case 1: 	//1 = Put
					resp = mainClient.put(cli, opr, clientId, quorum);
					for(int iter = 0; false && resp.getErr().contains("Failed"); iter++){
						System.out.println("Retrying for " + iter + "th time.");
						java.util.concurrent.TimeUnit.SECONDS.sleep(20*(1 << iter));
						resp = mainClient.put(cli, opr, clientId, quorum);
					}
					break;			
				case 2:		//2 = Get
					resp = mainClient.get(cli, opr, clientId, quorum);
					for(int iter=0; resp.getErr().contains("Failed"); iter++){
						java.util.concurrent.TimeUnit.SECONDS.sleep(20*(1 << iter));
						resp = mainClient.get(cli, opr, clientId, quorum);
					}
					break;				
				case 3:		//3 = Quit
					System.out.println("CLIENT: Quitting.");
					socket.close();
					context.term();
					return;
				default:
					resp = OpWire.Message.Response.newBuilder()
					      .setResponseTime(-100000.0)
					      .setErr("Operation was not found / supported")
					      .setClientStart(0.0)
					      .setQueueStart(0.0)
					      .setEnd(0.0)
					      .setClientid(clientId)
					      .setOptype("N/A")
					      .setTarget("N/A")
					      .build();
					quits = true;
					break;
			}
			payload = resp.toByteArray();
//			System.out.println("CLIENT: SENDING RESPONSE");
			socket.send(payload, 0);
		}	
		socket.close();
		context.term();
	}
	
}
