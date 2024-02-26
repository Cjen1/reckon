package cjen1.reckon.zkclient;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.function.Supplier;

import com.fasterxml.jackson.core.JsonProcessingException;

import org.apache.zookeeper.CreateMode;
import org.apache.zookeeper.KeeperException;
import org.apache.zookeeper.ZooDefs;
import org.apache.zookeeper.ZooKeeper;

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

  static String key_to_path(String k) { return "/" + k; }

  @Override
  public void Create(String k) throws ClientException {
    while(true) {
      try {
        client.create(
            key_to_path(k), 
            "NULL".getBytes(), 
            ZooDefs.Ids.OPEN_ACL_UNSAFE,
            CreateMode.PERSISTENT,
            null
            );
        System.err.println("Successful create");
        break;
      } catch (KeeperException.NodeExistsException ex) {
        break;
      } catch (Exception ex) {
        System.err.println(String.format("Failed to create key: %s", ex.toString()));
        // sleep to prevent thundering herd
        try {
          Thread.sleep(1000, 0);
        } catch (InterruptedException e) {}
      }
    }
  }

  @Override
  public void Put(String k, String v) throws ClientException {
    try {
      client.setData(
          key_to_path(k), 
          v.getBytes(), 
          -1// Match all versions
          );
    } catch (KeeperException ex) {
      throw new ClientException("Cause: " + ex.toString());
    } catch (InterruptedException ex) {
      throw new ClientException("Cause: " + ex.toString());
    }
  }

  @Override
  public String Get(String k) throws ClientException {
    try {
      return new String(
          client.getData(
            key_to_path(k),
            false,
            null
            ), 
          StandardCharsets.UTF_8);
    } catch (KeeperException ex) {
      throw new ClientException("Cause: " + ex.toString());
    } catch (InterruptedException ex) {
      throw new ClientException("Cause: " + ex.toString());
    }
  }
}

public class App {
  public static void main(String[] args) throws JsonProcessingException, IOException, ClientException {
    if (args.length != 4) {
      System.err.println("Incorrect number of arguments correct usage:\n<executable> <connection string> <client id> <new client per request> <number of client connections>");
      System.err.println("\tconnection string:            The zookeeper connection string of the form IP1:PORT1,IP2:Port2,... , eg. \"127.0.0.1:2379,127.0.0.1:2380\" .");
      System.err.println("\tclient id:                    The client id, eg \"test\".");
      System.err.println("\tnew client per request:       Boolean determining whether the client should use a new client per request.");
      System.err.println("\tnumber of client connections: The number of zookeeper client objects to use.");
      System.exit(1);
    }
    String connectString = args[0];
    boolean ncpr = Boolean.valueOf(args[1]);
    String clientId = args[2];
    int number_of_clients = Integer.valueOf(args[3]);

    Supplier<Client> cs = () -> {
      while(true) {
        try {
          return new ZKClient(connectString);
        } catch (IOException e){}
      }
    };

    Library.Run(cs, clientId, ncpr, number_of_clients); // 20 clients since each client can do 2k ops/s 

    System.err.println("Finished Library.Run");
    System.exit(0);
  }
}
