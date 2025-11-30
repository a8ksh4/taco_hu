#!/usr/bin/env python3

import socket
import struct
import time

import common.Api_pb2 as hudiy_api


# Adjust to your TCP endpoint (NOT the websocket port)
HUDIY_HOST = "127.0.0.1"
HUDIY_PORT = 44405  # example; set to your Api.tcp.port

# Hudiy frame header: <size: u32, messageId: u32, reserved: u32> (little-endian)
FRAME_HEADER_FMT = "<III"
FRAME_HEADER_SIZE = struct.calcsize(FRAME_HEADER_FMT)


def send_frame(sock: socket.socket, message_type: int, pb_msg) -> None:
    """Serialize protobuf message and send a single Hudiy frame."""
    payload = pb_msg.SerializeToString()
    size = len(payload)
    header = struct.pack(FRAME_HEADER_FMT, size, message_type, 0)
    sock.sendall(header + payload)


def recv_frame(sock: socket.socket):
    """Receive one Hudiy frame, return (message_type, payload_bytes)."""
    # Read fixed-size header
    header = b""
    while len(header) < FRAME_HEADER_SIZE:
        chunk = sock.recv(FRAME_HEADER_SIZE - len(header))
        if not chunk:
            raise RuntimeError("Connection closed while reading header")
        header += chunk

    size, message_type, reserved = struct.unpack(FRAME_HEADER_FMT, header)

    # Read payload
    payload = b""
    while len(payload) < size:
        chunk = sock.recv(size - len(payload))
        if not chunk:
            raise RuntimeError("Connection closed while reading payload")
        payload += chunk

    return message_type, payload


def send_hello(sock: socket.socket):
    """Send HelloRequest and wait for HelloResponse."""
    hello = hudiy_api.HelloRequest()
    hello.name = "raw-socket-volume-up"

    # Use API version from Constants enum
    hello.api_version.major = hudiy_api.Constants.API_MAJOR_VERSION
    hello.api_version.minor = hudiy_api.Constants.API_MINOR_VERSION

    send_frame(sock, hudiy_api.MESSAGE_HELLO_REQUEST, hello)

    # Block until we get HELLO_RESPONSE
    msg_type, payload = recv_frame(sock)
    if msg_type != hudiy_api.MESSAGE_HELLO_RESPONSE:
        raise RuntimeError(f"Expected HELLO_RESPONSE, got message type {msg_type}")

    resp = hudiy_api.HelloResponse()
    resp.ParseFromString(payload)

    if resp.result != hudiy_api.HelloResponse.HelloResponseResult.HELLO_RESPONSE_RESULT_OK:
        raise RuntimeError(f"Hudiy hello failed with result {resp.result}")

    print(
        f"HELLO OK: app {resp.app_version.major}.{resp.app_version.minor}, "
        f"api {resp.api_version.major}.{resp.api_version.minor}"
    )


def send_minimal_setup(sock: socket.socket):
    """Send a minimal SetStatusSubscriptions to keep Hudiy happy."""
    subs = hudiy_api.SetStatusSubscriptions()
    subs.subscriptions.append(
        hudiy_api.SetStatusSubscriptions.Subscription.MEDIA
    )

    send_frame(sock, hudiy_api.MESSAGE_SET_STATUS_SUBSCRIPTIONS, subs)


def send_volume_up(sock: socket.socket):
    """Send one DispatchAction('output_volume_up')."""
    action = hudiy_api.DispatchAction()
    action.action = "output_volume_up"

    send_frame(sock, hudiy_api.MESSAGE_DISPATCH_ACTION, action)
    print("Dispatched action: output_volume_up")


def main():
    with socket.create_connection((HUDIY_HOST, HUDIY_PORT)) as sock:
        sock.settimeout(5.0)

        # 1. Hello handshake
        send_hello(sock)

        # 2. Minimal subscriptions (as in your working Client-based example)
        send_minimal_setup(sock)

        # 3. Fire the action
        send_volume_up(sock)

        # Give Hudiy a moment to process before closing
        time.sleep(0.5)


if __name__ == "__main__":
    main()
