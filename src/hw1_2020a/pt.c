#include "os.h"

void page_table_update(uint64_t pt, uint64_t vpn, uint64_t ppn){
	uint64_t currentIndex;
	uint64_t* nextVirtual;

	// wrap with offset
	uint64_t nextPageTable = pt << 12;

	for (int i = 4; i > 0; i--) {
		// get 9 next bits
		currentIndex = (vpn >> (9 * i)) & 0x1ff;

		// get next address
		nextVirtual = (uint64_t*)(phys_to_virt(nextPageTable) + currentIndex * 8);

		// check invalid address
		if (*nextVirtual % 2 == 0 || *nextVirtual == NO_MAPPING) {
			// allocate new page and mark as valid
			nextPageTable = alloc_page_frame() << 12;

			// mark address as valid
			*nextVirtual = nextPageTable | 0x1;

		} else {
			nextPageTable = ((*nextVirtual) >> 12) << 12;
		}
	}

	// final iteration for last address
	currentIndex = vpn & 0x1ff;
	nextVirtual = (uint64_t*)(phys_to_virt(nextPageTable) + currentIndex * 8);

	// unmap/map according to ppn
	if (ppn == NO_MAPPING) {
		*nextVirtual = NO_MAPPING;
	} else {
		*nextVirtual = (ppn << 12) | 0x1;
	}
}

uint64_t page_table_query(uint64_t pt, uint64_t vpn){
	uint64_t currentIndex;
	uint64_t* nextVirtual;

	// wrap with offset
	uint64_t nextPageTable = pt << 12;

	for (int i = 4; i > 0; i--) {
		// get 9 next bits
		currentIndex = (vpn >> (9 * i)) & 0x1ff;

		// get next address
		nextVirtual = (uint64_t*)(phys_to_virt(nextPageTable) + currentIndex * 8);

		// check invalid address
		if (*nextVirtual % 2 == 0 || *nextVirtual == NO_MAPPING) {
			return NO_MAPPING;
		} else {
			nextPageTable = ((*nextVirtual) >> 12) << 12;
		}
	}

	// final iteration for last address
	currentIndex = vpn & 0x1ff;
	nextVirtual = (uint64_t*)(phys_to_virt(nextPageTable) + currentIndex * 8);

	// return NO_MAPPING or the address found
	if (*nextVirtual % 2 == 0 || *nextVirtual == NO_MAPPING) {
		return NO_MAPPING;
	} else {
		return *nextVirtual >> 12;
	}
}
