package cjen1.reckon.lib;

public class WaitGroup {
	private int jobs = 0;

	public synchronized void add(int i) {
		jobs += 1;
	}

	public synchronized void done() {
		if (--jobs == 0) {
			notifyAll();
		}
	}

	public synchronized void await() {
		while (jobs > 0) {
      try {
        wait();
      } catch (InterruptedException e) {
      }
		}
	}
}
