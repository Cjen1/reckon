package cjen1.reckon.lib;

import java.util.function.Consumer;

class TestClient implements Client {
  @Override
  public void Put(String k, String v) {
    return;
  }

  @Override
  public String Get(String k) {
    return "test_output";
  }

  @Override
  public void Create(String k) {
    Put(k, "CREATE");
  }
}
