package cjen1.reckon.zkclient;

import java.io.IOException;
import java.util.function.Consumer;
import java.util.function.Supplier;

import com.fasterxml.jackson.core.JsonProcessingException;

import org.apache.zookeeper.AsyncCallback;
import org.apache.zookeeper.CreateMode;
import org.apache.zookeeper.KeeperException;
import org.apache.zookeeper.ZooDefs;
import org.apache.zookeeper.ZooKeeper;
import org.apache.zookeeper.data.Stat;

import cjen1.reckon.lib.Client;
import cjen1.reckon.lib.ClientException;
import cjen1.reckon.lib.Library;

class ZKClient implements Client {
  static final int rc_ok = KeeperException.Code.OK.intValue();
  ZooKeeper client;
  public ZKClient(String connectString) throws IOException {
    client = new ZooKeeper(
        connectString,
        10000, // Session timeout milliseconds
        null
        );
  }

  static void run_callback(int rc, Runnable c, Consumer<Exception> e) {
    if (rc == KeeperException.Code.OK.intValue()) {
      c.run();
    } else {
      e.accept(new Exception("Failed to create with: " + KeeperException.Code.get(rc).toString()));
    }
  }

  static String key_to_path(String k) { return "/" + k; }

  @Override
  public void Create(String k, Runnable c, Consumer<Exception> e) {
    client.create(
        key_to_path(k), 
        "NULL".getBytes(), 
        ZooDefs.Ids.OPEN_ACL_UNSAFE,
        CreateMode.PERSISTENT,
        new AsyncCallback.StringCallback() {
          public void processResult(int rc, String result, Object ctx, String name) {
            run_callback(rc, c, e);
          }
        },
        null
        );
  }

  @Override
  public void Put(String k, String v, Runnable c, Consumer<Exception> e) {
    client.setData(
        key_to_path(k), 
        v.getBytes(), 
        -1,// Match all versions
        new AsyncCallback.StatCallback() {

          @Override
          public void processResult(int rc, String path, Object ctx, Stat stat) {
            run_callback(rc, c, e);
          }
        },
        null
        );
  }

	@Override
	public void Get(String k, Consumer<String> c, Consumer<Exception> e) {
    client.getData(
        key_to_path(k),
        false,
        new AsyncCallback.DataCallback() {
          @Override
          public void processResult(int rc, String path, Object ctx, byte[] data, Stat stat) {
            run_callback(rc, () -> c.accept(data.toString()), e);
          }
        },
        null
        );
	}
}

public class App {
  public static void main(String[] args) throws JsonProcessingException, IOException, ClientException {
    if (args.length != 3) {
      System.err.println("Incorrect number of arguments correct usage:\n<executable> <connection string> <client id> <new client per request>");
      System.err.println("\tconnection string:      The zookeeper connection string of the form IP1:PORT1,IP2:Port2,... , eg. \"127.0.0.1:2379,127.0.0.1:2380\" .");
      System.err.println("\tclient id:              The client id, eg \"test\".");
      System.err.println("\tnew client per request: Boolean determining whether the client should use a new client per request.");
      System.exit(1);
    }
    String connectString = args[0];
    boolean ncpr = false;
    String clientId = "";
     
    Supplier<Client> cb = () -> {
      while(true) {
        try {
          return new ZKClient(connectString);
        } catch (IOException e){}
      }
    };

    Library.Run(cb, clientId, ncpr);
  }
}
