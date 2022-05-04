package cjen1.reckon.lib;

import java.util.function.*;

public interface Client {
  public void Create(String k, Runnable c, Consumer<Exception> e);
	public void Put(String k, String v, Runnable c, Consumer<Exception> e);
	public void Get(String k, Consumer<String> c, Consumer<Exception> e);
}
