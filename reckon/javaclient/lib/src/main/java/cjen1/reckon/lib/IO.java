package cjen1.reckon.lib;

import java.io.IOException;
import java.nio.BufferUnderflowException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.nio.channels.WritableByteChannel;
import java.nio.charset.StandardCharsets;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

class IO {
	private ReadableByteChannel in = Channels.newChannel(System.in);
	private WritableByteChannel out = Channels.newChannel(System.out);

  public IO() {
	  in = Channels.newChannel(System.in);
	  out = Channels.newChannel(System.out);
  }

  public IO(ReadableByteChannel in_c, WritableByteChannel out_c) {
    in = in_c;
    out = out_c;
  }

	private void read_full(ByteBuffer b) throws IOException {
		int limit = b.remaining();
		int read = 0;
		while (read < limit) {
			read += in.read(b);
		}
	}

	private long read_uint4() throws IOException {
		ByteBuffer bb = ByteBuffer.allocate(4);
		bb.order(ByteOrder.LITTLE_ENDIAN);
		read_full(bb);
		bb.flip();
		try {
			int v = bb.getInt();
			return v & 0xffffffffL;
		} catch(BufferUnderflowException e) {
			throw new IOException("Unable to read bytes");
		}
	}

	private void write_uint4(long length) throws IOException {
		if (length > 8*8*8*8) {
			throw new IOException("Packet too large to write");
		}
		ByteBuffer bb = ByteBuffer.allocate(4);
		bb.order(ByteOrder.LITTLE_ENDIAN);
		bb.putInt((int)length);
		bb.flip();
		out.write(bb);
	}

	public String read_packet() throws IOException {
		long len = read_uint4();
		ByteBuffer bb = ByteBuffer.allocate((int)len);
		read_full(bb);
		bb.flip();
		return StandardCharsets.US_ASCII.decode(bb).toString();
	}

	public JsonNode read_packet(ObjectMapper om) throws IOException {
		return om.readTree(read_packet());
	}

	public void write_packet(String packet) throws IOException {
		int len = packet.length();
		write_uint4(len);
		ByteBuffer bb = StandardCharsets.US_ASCII.encode(packet);
		out.write(bb);
	}

	public void write_packet(Object packet, ObjectMapper om) throws IOException {
		write_packet(om.writeValueAsString(packet));
	}
}
