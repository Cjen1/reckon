package zookeeper_java;
import org.zeromq.ZMQ;
import org.apache.zookeeper.*;
import org.apache.zookeeper.data.*;
import java.util.*;
import OpWire.*;

public class Client implements org.apache.zookeeper.Watcher {
	public static final int CLIENT_PORT = 2181;
	public static final int QUORUM_PORT = 2888;
	public static final int ELECTION_PORT = 3888;
	public static final int SESSION_TIMEOUT = 10000; //Time to session timeout in ms
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
		return op;
	}

	public OpWire.Message.Response quit(ZMQ.Socket socket){
		OpWire.Message.Response resp = OpWire.Message.Response.newBuilder()
							     .setResponseTime(0.0)
							     .setErr("Socket Quitting")
							     .setMsg(".")
							     .build();
		return resp;
	}

	public OpWire.Message.Response put(ZooKeeper client, OpWire.Message.Operation opr){
		String err = "None";
		String path = "/" + opr.getPut().getKey();
		System.out.println("Decoded Path: " + path);
		String data = opr.getPut().getValue().toString();
		long start = System.nanoTime();
		try{
			client.create(path, data.getBytes(), ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);
		} catch(Exception e) {
			err = "Caught Exception: " + e.getMessage();
		}
		long stop = System.nanoTime();
		double duration = (stop - start + 0.0) / 1E9; // Duration in seconds.
		OpWire.Message.Response resp = OpWire.Message.Response.newBuilder()
							     .setResponseTime(duration)
							     .setErr(err)
							     .setMsg(".")
							     .build();
		System.out.println("Finished Put: err = " + err + ", duration = " + duration);
		return resp;
	}


	public OpWire.Message.Response get(ZooKeeper client, OpWire.Message.Operation opr){
		String err = "None";
		String path = "/" + opr.getGet().getKey();
		long start = System.nanoTime();
		try{

			client.getData(path, false, client.exists(path, false));
		} catch(Exception e) {
			err = "Caught Exception: " + e.getMessage();
		}
		long stop = System.nanoTime();
		double duration = (stop - start + 0.0) / 1E9; // Duration in seconds.
		OpWire.Message.Response resp = OpWire.Message.Response.newBuilder()
							     .setResponseTime(duration)
							     .setErr(err)
							     .setMsg(".")
							     .build();
		System.out.println("Finished get: err = " + err + ", duration = " + duration);
		return resp;
	}


	public static void main(String[] args) throws Exception {
		System.out.println("\n\n\nCLIENT: STARTING MAIN\n---@ port " + args[0] + "\n\n");
		Client mainClient = new Client();
		String port = args[0];
		String[] endpoints = args[1].split(",");
		
		ZMQ.Context context = ZMQ.context(1);
		ZMQ.Socket socket = context.socket(ZMQ.REP);
		
		String quorum = String.join(":" + CLIENT_PORT + ",", endpoints) + ":" + CLIENT_PORT;

		ZooKeeper cli = new ZooKeeper(quorum, SESSION_TIMEOUT, new Client());
		
		System.out.println("CLIENT: CREATED CONTEXT AND SOCKET\n---@ port " + port);

		String binding;
		boolean quits = false;
		OpWire.Message.Response resp = null;
		byte[] payload;
		int i = 0;
		binding = "tcp://127.0.0.1:" + port;
		socket.bind(binding);
		System.out.println("CLIENT: BOUND TO PORT " + port);
		while(!quits){
			i++;
			OpWire.Message.Operation opr = mainClient.receiveOp(socket);
			System.out.println("CLIENT: RECEIVED OPERATION " + i + " @ port " + port);
			switch(opr.getOpTypeCase().getNumber()){
				case 1: 	//1 = Put
					resp = mainClient.put(cli, opr);
					break;			
				case 2:		//2 = Get
					resp = mainClient.get(cli, opr);
					break;				
				case 3:		//3 = Quit
					resp = mainClient.quit(socket);
					quits = true;
					break;
				default:
					resp = OpWire.Message.Response.newBuilder()
					      .setResponseTime(0.0)
					      .setErr("Operation was not found / supported")
					      .setMsg(".")
					      .build();
					quits = true;
					break;
			}
			payload = resp.toByteArray();
			socket.send(payload, 0);
		}
	
		socket.close();
		context.term();
	}
}
