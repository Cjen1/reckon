package cjen1.reckon.lib;

import java.util.function.Consumer;

class TestClient implements Client {
	@Override
	public void Put(String k, String v, Runnable c, Consumer<Exception> e) {
    c.run();
	}

	@Override
	public void Get(String k, Consumer<String> c, Consumer<Exception> e) {
    c.accept("test_output");
	}

	@Override
	public void Create(String k, Runnable c, Consumer<Exception> e) {
    Put(k, "CREATE", c, e);
	}
}
