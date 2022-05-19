package cjen1.reckon.lib;

public interface Client {
  public void Create(String k) throws ClientException;
	public void Put(String k, String v) throws ClientException;
	public String Get(String k) throws ClientException;
}
