package daemon

import (
	"errors"
	"fmt"
	"net/netip"
	"sync"
)

type ipAllocator struct {
	prefix netip.Prefix
	base   uint32
	size   uint32
	used   []uint64
	next   uint32
	mu     sync.Mutex
}

func newIPAllocator(prefix netip.Prefix) (*ipAllocator, error) {
	prefix = prefix.Masked()
	ones := prefix.Bits()
	if !prefix.Addr().Is4() || ones < 0 || ones > 30 {
		return nil, fmt.Errorf("invalid workspace IPv4 subnet %s", prefix)
	}
	size := uint32(1) << uint32(32-ones)
	allocator := &ipAllocator{
		prefix: prefix,
		base:   addrToUint32(prefix.Addr()),
		size:   size,
		used:   make([]uint64, (size+63)/64),
		next:   2,
	}
	allocator.markUsed(0)
	allocator.markUsed(1)
	allocator.markUsed(size - 1)
	return allocator, nil
}

func (a *ipAllocator) allocate() (netip.Addr, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	for offset := uint32(0); offset < a.size; offset++ {
		index := (a.next + offset) % a.size
		if a.isUsed(index) {
			continue
		}
		a.markUsed(index)
		a.next = (index + 1) % a.size
		return uint32ToAddr(a.base + index), nil
	}
	return netip.Addr{}, errors.New("workspace subnet exhausted")
}

func (a *ipAllocator) reserve(ip netip.Addr) error {
	index, err := a.index(ip)
	if err != nil {
		return err
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.isUsed(index) {
		return fmt.Errorf("workspace IP %s is already reserved", ip)
	}
	a.markUsed(index)
	return nil
}

func (a *ipAllocator) release(ip netip.Addr) {
	index, err := a.index(ip)
	if err != nil || index == 0 || index == 1 || index == a.size-1 {
		return
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	a.clearUsed(index)
	if index < a.next {
		a.next = index
	}
}

func (a *ipAllocator) index(ip netip.Addr) (uint32, error) {
	if !ip.Is4() || !a.prefix.Contains(ip) {
		return 0, fmt.Errorf("workspace IP %s is outside subnet %s", ip, a.prefix)
	}
	index := addrToUint32(ip) - a.base
	if index >= a.size {
		return 0, fmt.Errorf("workspace IP %s is outside subnet %s", ip, a.prefix)
	}
	return index, nil
}

func (a *ipAllocator) isUsed(index uint32) bool {
	return a.used[index/64]&(uint64(1)<<(index%64)) != 0
}

func (a *ipAllocator) markUsed(index uint32) {
	a.used[index/64] |= uint64(1) << (index % 64)
}

func (a *ipAllocator) clearUsed(index uint32) {
	a.used[index/64] &^= uint64(1) << (index % 64)
}

func addrToUint32(addr netip.Addr) uint32 {
	bytes := addr.As4()
	return uint32(bytes[0])<<24 | uint32(bytes[1])<<16 | uint32(bytes[2])<<8 | uint32(bytes[3])
}

func uint32ToAddr(value uint32) netip.Addr {
	return netip.AddrFrom4([4]byte{
		byte(value >> 24),
		byte(value >> 16),
		byte(value >> 8),
		byte(value),
	})
}
