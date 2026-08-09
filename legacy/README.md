# Legacy baseline

This directory preserves byte-for-byte copies of the two application blobs present at commit `fe2b0332012ef9b03d73f6fc7b9ae1758f096b4b`. The manifest also points to the unchanged root `.gitattributes` blob.

The baseline exists only to make the rehabilitation auditable. It records observed behavior and known defects; it does not endorse them. It makes no authorship, ownership, or licensing claim. The copies are excluded from the wheel and production execution; they remain in the source archive solely for provenance review. The Python source uses a `.py.txt` suffix so the frozen development-server entry point is not presented as runnable application code.
