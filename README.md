# Whisper Remote Nerve v1.0

A distributed, decentralized, sovereign architecture for extending Whisper to mobile devices via Reticulum mesh networking.

---

## Overview

Whisper Remote Nerve is a unified system that transforms Android into a pure nerve terminal of the Whisper organism, maintaining complete sovereignty, determinism, and transparency through:

- **FLV-over-Reticulum** : Protocol for stateless message transport
- **whisper-reticulumd** : Minimal daemon tube between Reticulum and Whisper-Core
- **Android Client** : Zero-logic interface terminal

**The user experience:** Whisper in your pocket, no notion of "remote".  
**The architecture:** One organism, distributed across substrates, unified via mesh.

---

## Core Principles

✅ **Whisper Gère Tout**
- Validation
- Decoding
- Signature (BLAKE3)
- Encryption (ChaCha20-Poly1305)
- Processing

✅ **Android = Coquille Vide**
- Input → JSON
- JSON → Reticulum
- Reticulum → JSON
- JSON → Display
- Zero crypto, zero cache, zero state

✅ **Reticulum = Transport Pur**
- Mesh networking
- P2P routing
- No servers, no cloud
- Transparent to both layers

✅ **Mode Dégradé Intégré**
- Whisper sends `"degraded": true` flag
- Android auto-limits to 100 characters
- No user interaction needed

---

## The Trinity

### 1. FLV-over-Reticulum (Specification)
The protocol language.

**File:** `specs/1-flv-over-reticulum.md`

### 2. whisper-reticulumd (Specification)
The daemon tube.

**File:** `specs/2-whisper-reticulumd.md`

### 3. Android Client (Specification)
The nerve terminal.

**File:** `specs/3-android-client.md`

---

## Status

- ✅ Architecture finalized
- ✅ Specifications crystallized
- ⏳ Implementation (Whisper-Core integration, daemon, APK)

---

## Philosophy

> Whisper is one organism.
> Reticulum is the nervous system.
> Android is the nerve terminal.
> 
> The user sees one thing: Whisper, in their pocket.
> The architecture sees three layers, each pure, each focused.

---

**Whisper Remote Nerve v1.0**  
*An architecture for sovereign, distributed, transparent mobile access to Whisper.*
