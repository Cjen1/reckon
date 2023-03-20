package cjen1.reckon.lib;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;
import java.util.function.Supplier;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;


class Response {
  public Response(double t_submitted, double t_result, String result, String op_kind, String clientid) {
    this.t_submitted = t_submitted;
    this.t_result = t_result;
    this.result = result;
    this.op_kind = op_kind;
    this.clientid = clientid;
  }

  public String kind = "result";
  public double t_submitted;
  public double t_result;
  public String result;
  public String op_kind;
  public String clientid;
  public Map<String, String> other = Collections.emptyMap();
}

public class Library {
  private static double to_epoch(Instant t) {
    double seconds = (double)t.getEpochSecond();
    double nanos = (double)t.getNano() / 1e9;
    double res = seconds + nanos;
    return res;
  }

  private static void perform(String clientid, Client cli, JsonNode operation, Consumer<Response> response_callback, Boolean prereq) {
    JsonNode payload = operation.get("payload");
    final String kind = payload.get("kind").asText();
    Instant start = Instant.now();
    try {
      switch (kind) {
        case "write":
          if (prereq) {
            cli.Create(
                payload.get("key").asText()
                );
            Instant end = Instant.now();
            response_callback.accept(new Response(
                to_epoch(start),
                to_epoch(end),
                "Success",
                kind,
                clientid
                ));
          } else {
            cli.Put(
                payload.get("key").asText(), 
                payload.get("value").asText()
                );
            Instant end = Instant.now();
            response_callback.accept( new Response(
                to_epoch(start),
                to_epoch(end),
                "Success",
                kind,
                clientid
                ));
          }
          break;
        case "read":
          cli.Get(
              payload.get("key").asText()
              );
          Instant end = Instant.now();
          response_callback.accept( new Response(
              to_epoch(start),
              to_epoch(end),
              "Success",
              kind,
              clientid
              ));
          break;
        default:
          response_callback.accept( new Response(
              (float)-1.,
              (float)-1.,
              String.format("Error operation %s was not supported", kind),
              kind,
              clientid
              ));
          break;
      }
    } catch (ClientException ex) {
      response_callback.accept( new Response(
          (float)-1.,
          (float)-1.,
          String.format("Failed with client exception: %s", ex.toString()),
          kind,
          clientid
          ));
    }
  }

  private static void unrecognised_message(JsonNode msg) {
    System.err.println("Got an unrecognised message...");
    System.err.println(msg.asText());
    System.err.println("Quitting due to an unrecognised message");
    System.exit(1);
  }

  public static void Run(IO io, Supplier<Client> getClient, String clientid, boolean new_client_per_request, int number_client_objs) throws IOException, JsonProcessingException, ClientException {
    ObjectMapper om = new ObjectMapper();
    System.err.println("Client: Starting run");

    //ExecutorService ex = Executors.newFixedThreadPool(30000);
    ExecutorService ex = Executors.newCachedThreadPool();

    System.err.println("Phase 1: preload");
    ArrayList<JsonNode> operations = new ArrayList<JsonNode>();
    boolean got_finalise = false;
    WaitGroup preload_wg = new WaitGroup();
    Client preloadClient = getClient.get();
    do {
      JsonNode data = io.read_packet(om);
      switch( data.get("kind").asText() ) {
        case "preload":
          if (data.get("prereq").asBoolean()) {
            preload_wg.add(1);
            ex.execute(() -> 
                perform(
                  clientid,
                  preloadClient,
                  data.get("operation"),
                  (Response R)->preload_wg.done(),
                  true
                  ));
          } else {
            operations.add(data.get("operation"));
          }
          break;
        case "finalise":
          got_finalise = true;
          break;
        default:
          unrecognised_message(data);
          break;
      }
    } while(!got_finalise);

    // Sort requests to be in ascending start order
    operations.sort((JsonNode a, JsonNode b)->{
      return Double.compare(
      a.get("time").asDouble(),
      b.get("time").asDouble()
      );
    });

    System.err.println(String.format("Phase 1: Preload requests loaded, and prerequisites dispatched"));

    preload_wg.await();

    System.err.println(String.format("Phase 1: Preload complete got %d requests", operations.size()));

    Client[] clis = new Client[number_client_objs];
    for (int i = 0; i < number_client_objs; i ++) {
      clis[i] = getClient.get();
    }

    System.err.println("Phase 2: readying");
    io.write_packet(om.readTree("{\"kind\": \"ready\"}"), om);

    System.err.println("Phase 3: execute");
    System.err.println("Phase 3: awaiting start");
    boolean got_start = false;
    do {
      JsonNode data = io.read_packet(om);
      switch( data.get("kind").asText()) {
        case "start":
          got_start = true;
          break;
        default:
          unrecognised_message(data);
          break;
      }
    } while(!got_start);

    System.err.println("Phase 3: starting");
    ConcurrentMap<Response,Integer> resp_map = new ConcurrentHashMap<Response,Integer>();
    WaitGroup execute_wg = new WaitGroup();
    double start_time = to_epoch(Instant.now()); 

    Consumer<Response> resp_callback = (Response r)->{
      resp_map.put(r, Integer.valueOf(0));
      execute_wg.done();
    };

    double max_behind = 0;
    int cmd_num = 0;
    for (JsonNode operation : operations) {
      double target = operation.get("time").asDouble();
      Client c = new_client_per_request ? getClient.get() : clis[cmd_num++ % number_client_objs];

      // Sleep until target
      while(true) {
        double current = to_epoch(Instant.now()) - start_time;
        double diff = target - current;

        // rounds down on cast to long
        double diff_ms = diff * 1000;
        max_behind = Math.max(max_behind, -diff_ms);
        if (diff_ms < 0.1) { // within 100us
          break;
        }

        double diff_rem_ms = diff_ms - Math.floor(diff_ms);
        double diff_rem_ns = diff_rem_ms * 1e6;
        long sleep_time_ms = (long)(diff_ms);
        int sleep_time_rem_ns = (int)(diff_rem_ns);
        try {
          Thread.sleep(sleep_time_ms, sleep_time_rem_ns);
        } catch (InterruptedException e) {}
      }

      execute_wg.add(1);
      ex.execute(() ->
          perform(
            clientid,
            c,
            operation,
            resp_callback,
            false
            ));
    }

    System.err.println(String.format("Phase 3: fell behind by at most %.3f ms", max_behind));

    System.err.println("Phase 3: waiting for requests to finish");
    execute_wg.await();

    System.err.println("Phase 4: collate");
    // Take responses from map, and sort by submit time
    ArrayList<Response> responses = new ArrayList<Response>(resp_map.size());
    for (Response r : resp_map.keySet()) {
      responses.add(r);
    }
    responses.sort((Response l, Response r) -> Double.compare(l.t_submitted, r.t_submitted));

    // Write responses to disk
    for (Response r : responses) {
      io.write_packet(r, om);
    }

    System.err.println(String.format("Phase 4: Sent %d results", responses.size()));

    System.err.println("Phase 5: finalise");
    io.write_packet(om.readTree("{\"kind\":\"finished\"}"), om);

    ex.shutdownNow();
    System.err.println("Phase 5: exit");
    System.exit(0);
  }

  public static void Run(Supplier<Client> cb, String clientid, boolean new_client_per_request, int number_client_objs) throws IOException, JsonProcessingException, ClientException {
	  Run(new IO(), cb, clientid, new_client_per_request, number_client_objs);
  }
}
