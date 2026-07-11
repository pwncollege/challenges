package daemon

import (
	"net/netip"
	"sync"
	"testing"
)

func TestIPAllocatorReserveReleaseAndExhaustion(t *testing.T) {
	allocator, err := newIPAllocator(netip.MustParsePrefix("192.0.2.0/29"))
	if err != nil {
		t.Fatal(err)
	}
	if err := allocator.reserve(netip.MustParseAddr("192.0.2.4")); err != nil {
		t.Fatal(err)
	}

	want := []netip.Addr{
		netip.MustParseAddr("192.0.2.2"),
		netip.MustParseAddr("192.0.2.3"),
		netip.MustParseAddr("192.0.2.5"),
		netip.MustParseAddr("192.0.2.6"),
	}
	for _, expected := range want {
		actual, err := allocator.allocate()
		if err != nil {
			t.Fatal(err)
		}
		if actual != expected {
			t.Fatalf("allocated %s, want %s", actual, expected)
		}
	}
	if _, err := allocator.allocate(); err == nil {
		t.Fatal("expected exhausted subnet")
	}

	allocator.release(want[1])
	actual, err := allocator.allocate()
	if err != nil {
		t.Fatal(err)
	}
	if actual != want[1] {
		t.Fatalf("allocated %s after release, want %s", actual, want[1])
	}
}

func TestIPAllocatorConcurrentAllocationsAreUnique(t *testing.T) {
	allocator, err := newIPAllocator(netip.MustParsePrefix("198.51.100.0/24"))
	if err != nil {
		t.Fatal(err)
	}

	const count = 100
	addresses := make(chan netip.Addr, count)
	errors := make(chan error, count)
	var group sync.WaitGroup
	for range count {
		group.Add(1)
		go func() {
			defer group.Done()
			address, err := allocator.allocate()
			if err != nil {
				errors <- err
				return
			}
			addresses <- address
		}()
	}
	group.Wait()
	close(addresses)
	close(errors)
	for err := range errors {
		t.Fatal(err)
	}

	seen := map[netip.Addr]struct{}{}
	for address := range addresses {
		if _, exists := seen[address]; exists {
			t.Fatalf("allocated %s more than once", address)
		}
		seen[address] = struct{}{}
	}
	if len(seen) != count {
		t.Fatalf("allocated %d unique addresses, want %d", len(seen), count)
	}
}
