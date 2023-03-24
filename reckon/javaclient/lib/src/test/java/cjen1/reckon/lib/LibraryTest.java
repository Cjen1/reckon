/*
 * This Java source file was generated by the Gradle 'init' task.
 */
package cjen1.reckon.lib;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.channels.FileChannel;
import java.time.Instant;

import com.fasterxml.jackson.core.JsonProcessingException;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.atomic.AtomicInteger;

import java.util.function.*;

class LibraryTest {

  @Test void run() throws JsonProcessingException, IOException, ClientException {
    RandomAccessFile fin = new RandomAccessFile("in.bin", "r");
    FileChannel in_c = fin.getChannel();
    RandomAccessFile fout = new RandomAccessFile("out.bin", "rw");
    FileChannel out_c = fout.getChannel();

    IO io = new IO(in_c, out_c); 

    Library.Run(io, ()->new TestClient(), "test client", false, 2);

    fin.close();
    fout.close();
  }

  private static double to_epoch(Instant t) {
    double seconds = (double)t.getEpochSecond();
    double nanos = (double)t.getNano() / 1e9;
    double res = seconds + nanos;
    return res;
  }

  @Test void wait_group_waits() {
    WaitGroup wg = new WaitGroup();
    ExecutorService ex = Executors.newCachedThreadPool();
    AtomicInteger completed = new AtomicInteger(0);
    double start = to_epoch(Instant.now());
    for (int i = 0; i < 1000; i ++) {
      wg.add(1);
      ex.execute(() -> {
        try {
          Thread.sleep(2000);
        } catch (InterruptedException e) {}
        completed.incrementAndGet();
        wg.done();
      });
    }
    double dispatch_end = to_epoch(Instant.now()); 

    wg.await();
    double end = to_epoch(Instant.now()); 
    System.err.println(String.format("Threads took %.3f ms", (end - start) * 1000));
    System.err.println(String.format("Dispatch took %.3f ms", (dispatch_end - start) * 1000));
    assert(end - start > 1);
  }

  static void run_and_report(ExecutorService ex, int n) {
    WaitGroup wg = new WaitGroup();
    AtomicInteger completed = new AtomicInteger(0);
    double start = to_epoch(Instant.now());
    for (int i = 0; i < n; i ++) {
      wg.add(1);
      ex.execute(() -> {
        completed.incrementAndGet();
        wg.done();
      });
    }
    double dispatch_end = to_epoch(Instant.now()); 
    wg.await();
    double end = to_epoch(Instant.now()); 
    System.err.println(String.format("Threads: %.3f ms, Dispatch: %.3f ms, Dispatch Rate: %.3f",
          (end - start) * 1000,
          (dispatch_end - start) * 1000,
          n / (dispatch_end - start)
          ));
  }

  private class Pair<A,B> {
    public final A a;
    public final B b;

    public Pair(A a, B b) {
      this.a = a;
      this.b = b;
    }
  }

  @Test void load_generator_perf() {
    int n = 1000000;

    var tps = new ArrayList<Pair<String, Supplier<ThreadPoolExecutor>>>();

    tps.add(
        new Pair<String, Supplier<ThreadPoolExecutor>>(
          "TP(0, MAX, SynchronousQueue)", 
          () -> new ThreadPoolExecutor(0, Integer.MAX_VALUE, 60L, TimeUnit.SECONDS, new SynchronousQueue<Runnable>()))
        );

    tps.add(
        new Pair<String, Supplier<ThreadPoolExecutor>>(
          "TP(10, MAX, SynchronousQueue)", 
          () -> new ThreadPoolExecutor(10, Integer.MAX_VALUE, 60L, TimeUnit.SECONDS, new SynchronousQueue<Runnable>()))
        );

    tps.add(
        new Pair<String, Supplier<ThreadPoolExecutor>>(
                 "TP(0, MAX, LinkedBlockingQueue)", 
          () -> new ThreadPoolExecutor(10, Integer.MAX_VALUE, 60L, TimeUnit.SECONDS, new LinkedBlockingQueue<Runnable>()))
        );

    tps.add(
        new Pair<String, Supplier<ThreadPoolExecutor>>(
          "TP(10, MAX, LinkedBlockingQueue)", 
          () -> new ThreadPoolExecutor(10, Integer.MAX_VALUE, 60L, TimeUnit.SECONDS, new LinkedBlockingQueue<Runnable>()))
        );

    for (Pair<String,Supplier<ThreadPoolExecutor>> x : tps) {
      System.err.println(x.a);

      System.err.println("non-prestart");
      var tp_nps = x.b.get();
      run_and_report(x.b.get(), n);
      System.err.println("--------------------");
      tp_nps.shutdown();

      System.err.println("prestart");
      var tp_np = x.b.get();
      tp_np.prestartAllCoreThreads();
      run_and_report(tp_np, n);
      tp_np.shutdown();

      System.err.println("--------------------------------------------------");
    }
  }
}