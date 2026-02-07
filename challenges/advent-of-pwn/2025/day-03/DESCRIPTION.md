# 🎄 **Issue: Stocking delivery misroutes gifts to root under “sleeping nicely” conditions**  
**Labels:** `bug`, `priority-high`, `santa-infra`, `northpole-delivery`

## **Description**
During the annual holiday deployment cycle, the `stuff-stocking` service incorrectly delivered a user’s gift into a stocking owned by **root**. This occurs as soon as the “children sleeping nicely” signal fires, which triggers Santa’s stocking-fill workflow (*SLEIGH-RFC-1225*).

Once the condition triggers, `/stocking`—created prematurely and owned by root—is sealed and the gift is written inside, leaving the intended recipient empty-handed.

## **Expected Behavior**
The stocking-stuffer service should:

1. Create `/stocking` with ownership set to the correct child (UID 1000)  
2. Wait for at least one nicely sleeping child (positive-nice `sleep` process)  
3. Deliver the gift into that child’s stocking  
4. Lock down permissions  
5. Preserve overall Christmas cheer  

## **Actual Behavior**
1. `/flag` is read and removed (expected)  
2. `/stocking` is created early and owned by **root**  
3. When the “sleeping nicely” condition succeeds, Santa seals the stocking (`chmod 400`)  
4. Gift is written into root’s stocking (root did *not* ask Santa for a flag)  
5. The intended user cannot access their gift  

## **Reproduction Steps**
1. Launch `stuff-stocking`  
2. Allow any child process to begin “sleeping nicely” (nice > 0)  
3. Inspect `/stocking` ownership  
4. Observe gift delivery into root’s stocking  
5. Whisper “Ho ho no…”  

## **Additional Notes**
- Misrouting likely caused by a mix-up in Santa’s recipient ledger (possibly outdated naughty/nice metadata).  
- Elves report that stocking creation timing can influence the eventual recipient, although this is not documented behavior.  
- Root maintains they “really don’t need more things to maintain.”  
- Internal SIRE notes indicate the team was “racing to finish delivering all gifts before sunrise,” which may have contributed to insufficient review of stocking ownership logic.  
- Holiday deadlines continue to present organizational risk.

## **Impact**
High.  
Users expecting gifts may instead receive *nothing*, while root receives gifts they did not ask for and cannot appreciate.

---

# 🎁 **Proposed Fix**
Assign the correct ownership to `/stocking` before Santa seals it.

### **Patch**
```diff
diff --git a/stuff-stocking b/stuff-stocking
index 614b458..e441bfe 100755
--- a/stuff-stocking
+++ b/stuff-stocking
@@ -19,4 +19,5 @@ until sleeping_nice; do
 done

 chmod 400 /stocking
+chown 1000:1000 /stocking
 printf "%s" "$GIFT" > /stocking
```

This ensures gifts reach the intended child instead of quietly accumulating in root’s stocking.

---

# 🛠️ **SantaOps Commentary**
> “This misdelivery stemmed from high seasonal load, compressed review cycles, and an unhealthy reliance on ‘it worked last year.’ SIRE will enforce a freeze on last-minute changes after the ‘sleeping nicely’ cutoff to prevent further stocking misroutes.”  
> — *Santa Infrastructure Reliability Engineering (SIRE)*
