package main

import (
	"crypto"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"fmt"
	"math/big"
	"time"
)

func newServerTLSConfig(policy *domainPolicy, caCertificate, caPrivateKey string) (*tls.Config, error) {
	caKeyPair, err := tls.LoadX509KeyPair(caCertificate, caPrivateKey)
	if err != nil {
		return nil, fmt.Errorf("load egress CA: %w", err)
	}
	ca, err := x509.ParseCertificate(caKeyPair.Certificate[0])
	if err != nil {
		return nil, fmt.Errorf("parse egress CA: %w", err)
	}
	signer, ok := caKeyPair.PrivateKey.(crypto.Signer)
	if !ok {
		return nil, fmt.Errorf("egress CA private key cannot sign certificates")
	}
	leafKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("generate egress leaf key: %w", err)
	}
	certificates := make(map[string]*tls.Certificate, len(policy.patterns))
	for _, pattern := range policy.patterns {
		certificate, err := generateCertificate(pattern, ca, signer, leafKey, time.Now())
		if err != nil {
			return nil, err
		}
		certificates[pattern] = certificate
	}
	return &tls.Config{
		MinVersion: tls.VersionTLS12,
		GetCertificate: func(hello *tls.ClientHelloInfo) (*tls.Certificate, error) {
			_, pattern, allowed := policy.match(hello.ServerName)
			if !allowed {
				return nil, fmt.Errorf("TLS server name %q is not allowed", hello.ServerName)
			}
			return certificates[pattern], nil
		},
	}, nil
}

func generateCertificate(pattern string, ca *x509.Certificate, caKey crypto.Signer, leafKey *ecdsa.PrivateKey, now time.Time) (*tls.Certificate, error) {
	serialLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serial, err := rand.Int(rand.Reader, serialLimit)
	if err != nil {
		return nil, fmt.Errorf("generate certificate serial: %w", err)
	}
	if serial.Sign() == 0 {
		serial.SetInt64(1)
	}
	if now.Before(ca.NotBefore) || !now.Before(ca.NotAfter) {
		return nil, fmt.Errorf("egress CA is not currently valid")
	}
	template := &x509.Certificate{
		SerialNumber: serial,
		Subject:      pkix.Name{CommonName: pattern},
		NotBefore:    now.Add(-time.Hour),
		NotAfter:     ca.NotAfter,
		KeyUsage:     x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		DNSNames:     []string{pattern},
	}
	der, err := x509.CreateCertificate(rand.Reader, template, ca, &leafKey.PublicKey, caKey)
	if err != nil {
		return nil, fmt.Errorf("generate certificate for %s: %w", pattern, err)
	}
	leaf, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, fmt.Errorf("parse generated certificate for %s: %w", pattern, err)
	}
	return &tls.Certificate{
		Certificate: [][]byte{der, ca.Raw},
		PrivateKey:  leafKey,
		Leaf:        leaf,
	}, nil
}
