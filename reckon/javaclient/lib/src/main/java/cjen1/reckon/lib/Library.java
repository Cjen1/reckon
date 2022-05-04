package cjen1.reckon.lib;

import java.util.ArrayList;
import java.io.IOException;
import java.time.*;
import java.util.function.*;
import java.util.Collections;
import java.util.Map;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;


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

  private static void perform(String clientid, Supplier<Client> getClient, JsonNode operation, Consumer<Response> response_callback, Boolean prereq) {
    Client cli = getClient.get();
    JsonNode payload = operation.get("payload");
    final String kind = payload.get("kind").asText();
    Instant start = Instant.now();
    Consumer<String> op_callback = (String result) -> {
      Instant end = Instant.now();
      response_callback.accept(new Response(
            to_epoch(start),
            to_epoch(end),
            result,
            kind,
            clientid
            ));
    };
    switch (kind) {
      case "write":
        if (prereq) {
          cli.Create(
              payload.get("key").asText(), 
              ( ) -> { op_callback.accept("Success");},
              (Exception e) -> { op_callback.accept(String.format("Failed: %s", e.toString())); }
              );
        } else {
          cli.Put(
              payload.get("key").asText(), 
              payload.get("value").asText(), 
              ( ) -> { op_callback.accept("Success");},
              (Exception e) -> { op_callback.accept(String.format("Failed: %s", e.toString())); }
              );
        }
        break;
      case "read":
        cli.Get(
            payload.get("key").asText(), 
            (String s) -> { op_callback.accept("Success");},
            (Exception e) -> { op_callback.accept(String.format("Failed: %s", e.toString())); }
          );
        break;
      default:
        response_callback.accept(
            new Response(
              (float)-1.,
              (float)-1.,
              String.format("Error operation %s was not supported", kind),
              kind,
              clientid
              ));
        break;
    }
  }

  private static void unrecognised_message(JsonNode msg) {
    System.err.println("Got an unrecognised message...");
    System.err.println(msg.asText());
    System.err.println("Quitting due to an unrecognised message");
    System.exit(1);
  }

  public static void Run(IO io, Supplier<Client> cb, String clientid, boolean new_client_per_request) throws IOException, JsonProcessingException, ClientException {
    ObjectMapper om = new ObjectMapper();
    System.err.println("Client: Starting run");

    Supplier<Client> getClient = cb;
    if (!new_client_per_request) {
      Client c = cb.get();
      getClient = () -> { return c; };
    }

    System.err.println("Phase 1: preload");
    ArrayList<JsonNode> operations = new ArrayList<JsonNode>();
    boolean got_finalise = false;
    WaitGroup preload_wg = new WaitGroup();
    do {
      JsonNode data = io.read_packet(om);
      switch( data.get("kind").asText() ) {
        case "preload":
          if (data.get("prereq").asBoolean()) {
            preload_wg.add(1);
            perform(
                clientid,
                getClient,
                data.get("operation"),
                (Response R)->preload_wg.done(),
                true
                );
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
    preload_wg.await();

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
    ArrayList<Response> responses = new ArrayList<Response>(operations.size());
    WaitGroup execute_wg = new WaitGroup();
    double start_time = to_epoch(Instant.now()); 

    for (JsonNode operation : operations) {
      double target = operation.get("time").asDouble();
      while(true) {
        double current = to_epoch(Instant.now()) - start_time;
        double diff = target - current;
        long sleep_time_ms = (long)(diff * 1000.);

        if (sleep_time_ms > 0) {
          try {
            Thread.sleep(sleep_time_ms);
          } catch (InterruptedException e) {}
        } else {
          // Should not wait longer => break out of loop
          break;
        }
        execute_wg.add(1);
        perform(
            clientid,
            getClient,
            operation,
            (Response r)->{ 
              responses.add(r);
              execute_wg.done();
            },
            false);
      }
    }

    System.err.println("Phase 3: waiting for requests to finish");
    execute_wg.await();

    System.err.println("Phase 4: collate");
    for (Response r : responses) {
      io.write_packet(r, om);
    }
    System.err.println("Phase 4: results sent");

    System.err.println("Phase 5: finalise");
    io.write_packet(om.readTree("{\"kind\":\"finished\"}"), om);
    System.err.println("Phase 5: exit");
  }

  public static void Run(Supplier<Client> cb, String clientid, boolean new_client_per_request) throws IOException, JsonProcessingException, ClientException {
	  Run(new IO(), cb, clientid, new_client_per_request);
  }
}
