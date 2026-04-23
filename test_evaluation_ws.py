"""
WebSocket Test Client for Evaluation Server
Tests the real-time evaluation data stream
"""
import asyncio
import websockets
import json
import sys

async def test_evaluation_stream():
    uri = "ws://localhost:8001/ws/evaluation"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            print("\nReceiving evaluation data (will show first 5 packets)...\n")
            
            for i in range(5):
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)
                    
                    print(f"{'='*70}")
                    print(f"Packet #{data.get('packet_id', 'N/A')}")
                    print(f"{'='*70}")
                    
                    # Classical Metrics
                    classical = data.get('classical', {})
                    print(f"\n📊 CLASSICAL BASELINE:")
                    print(f"   Accuracy: {classical.get('accuracy', 0):.2f}%")
                    print(f"   F1 Score: {classical.get('f1', 0):.4f}")
                    print(f"   FPR: {classical.get('fpr', 0):.4f}")
                    print(f"   FNR: {classical.get('fnr', 0):.4f}")
                    print(f"   Avg Confidence: {classical.get('avg_confidence', 0):.4f}")
                    print(f"   Avg Latency: {classical.get('avg_latency', 0):.4f} ms")
                    
                    # Quantum Metrics
                    quantum = data.get('quantum', {})
                    print(f"\n🔮 QUANTUM-INSPIRED:")
                    print(f"   Accuracy: {quantum.get('accuracy', 0):.2f}%")
                    print(f"   F1 Score: {quantum.get('f1', 0):.4f}")
                    print(f"   FPR: {quantum.get('fpr', 0):.4f}")
                    print(f"   FNR: {quantum.get('fnr', 0):.4f}")
                    print(f"   Avg Confidence: {quantum.get('avg_confidence', 0):.4f}")
                    print(f"   Avg Latency: {quantum.get('avg_latency', 0):.4f} ms")
                    
                    # Explanation
                    explanation = data.get('explanation', 'N/A')
                    print(f"\n💡 EXPLANATION:")
                    print(f"   {explanation}")
                    
                    # Attack Type
                    attack_type = data.get('attack_type', 'Unknown')
                    print(f"\n🎯 GROUND TRUTH: {attack_type}")
                    print()
                    
                except asyncio.TimeoutError:
                    print(f"❌ Timeout waiting for packet {i+1}")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    break
            
            print("\n✅ Test completed successfully!")
            print("The evaluation server is streaming data correctly.")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket connection error: {e}")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"❌ Connection refused. Is the evaluation server running on port 8001?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*70)
    print("EVALUATION SERVER WEBSOCKET TEST")
    print("="*70)
    asyncio.run(test_evaluation_stream())
