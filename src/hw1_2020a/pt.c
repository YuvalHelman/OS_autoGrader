
#include "os.h"
#include <stdlib.h>
#include <stdio.h>

#define LEVELS (5)

void page_table_update(uint64_t pt, uint64_t vpn, uint64_t ppn) {
	int i;
	uint64_t *va = NULL, vpn_addr, pte_tmp = (pt << 12);

	for (i = 0; i < LEVELS; i++) {
		va = ((uint64_t *) phys_to_virt(pte_tmp & (~0xfff)));
		vpn_addr = ((vpn >> (9*(LEVELS - 1 - i))) & 0x1ff);
		pte_tmp = va[vpn_addr];
		if (!(pte_tmp & 0x1)) {
			if (ppn == NO_MAPPING) return;
			pte_tmp = ((alloc_page_frame() << 12) | 0x1);
		}
		va[vpn_addr] = (i != 4) ? pte_tmp : ((ppn != NO_MAPPING) ? ((ppn << 12) | 0x1) : (va[vpn_addr] & (~0x1)));
	}
}

uint64_t page_table_query(uint64_t pt, uint64_t vpn) {
	int i;
	uint64_t *va = NULL, pte_tmp = (pt << 12);

	for (i = 0; i < LEVELS; i++) {
		va = (uint64_t *) phys_to_virt(pte_tmp & (~0xfff));
		pte_tmp = va[((vpn >> (9*(LEVELS - 1 - i))) & 0x1ff)];
		if (!(pte_tmp & 0x1)) return NO_MAPPING;
	}
	return (pte_tmp >> 12);
}


