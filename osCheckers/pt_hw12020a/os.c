//---------------------------------------------
//a Page size is 4KB, so the first 12 bits specify it
//
//          PHYSICAL PAGES INFO:
//The size of a page table entry is 64 bits. Bit 0 is the
//valid bit. Bits 1–11 are unused and must be set to zero. (This means that our target CPU does
//not implement page access rights.) The top 52 bits contain the page frame number that this entry
//points to,
//
//          Virtual Pages Info:
//The virtual address size of our hardware is 64 bits, of which only the lower 57 bits are
//used for translation. The top 7 bits are guaranteed to be identical to bit 56, i.e., they
//are either all ones or all zeroes.
//
//                            7     +     (45)            +   12
// Virtual Page structure: sign-ext +  5 layers of 9 bits + offset
//
//Page Tables maps 'virtual pages' to 'physical pages' ( VPN -> PPN)
//
//      Two Functions on OS.c:
//1. alloc_page_frame(void) : allocate a physical page and return its physical page number.
//
//2. phys_to_virt(uint64_t phys_addr) : The valid inputs to phys to virt() are addresses that reside in
//physical pages that were previously returned by alloc page frame(). If it is called with an invalid input,
//it returns NULL.
//
//
//      Two function to check:
//1. void page table update(uint64 t pt, uint64 t vpn, uint64 t ppn):
//   pt - the physical page number (returned from alloc_page_frame() )
//   vpn: the virtual page number to map\unmap
//   ppn: NO_MAPPING means destroy a mapping. otherwise, the physical page number that vpn should be mapped to.
//  -- This function creates\destroys virtual memory mapping in a page table.
//
//2. uint64 t page table query(uint64 t pt, uint64 t vpn):
//   This function returns the physical page number that vpn is mapped to, or NO MAPPING if no
//   mapping exists. The meaning of the pt argument is the same as with page table update().
//
//---------------------------------------------


#define _GNU_SOURCE

#include "math.h"

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <err.h>
#include <sys/mman.h>

#include "os.h"


#include <inttypes.h>
#include <execinfo.h>
#include <time.h>

#define VPN_MASK 0x1FFFFFFFFFFF
#define PPN_MASK 0xFFFFFFFFFFFFF

/* 2^20 pages ought to be enough for anybody */
#define NPAGES	(1024*1024)
#define EXIT_FAILED -1
#define EXIT_SUCCESS 0
#define BASIC_FUNC_FAILED 242

static void* pages[NPAGES];

uint64_t alloc_page_frame(void)
{
	static uint64_t nalloc;
	uint64_t ppn;
	void* va;

	if (nalloc == NPAGES)
		errx(1, "out of physical memory");

	/* OS memory management isn't really this simple */
	ppn = nalloc;
	nalloc++;

	va = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
	if (va == MAP_FAILED)
		err(1, "mmap failed");

	pages[ppn] = va;	
	return ppn;
}

void* phys_to_virt(uint64_t phys_addr)
{ // takes phys_addr , a physical address, go to the page of the given page number, and on to it's offset.
  // returns the address in memory of this.
	uint64_t ppn = phys_addr >> 12;
	uint64_t off = phys_addr & 0xfff;
	void* va = NULL;

	if (ppn < NPAGES)
		va = pages[ppn] + off;

	return va;
}

// TESTS FUNCTIONS

void tester_update_ppn_mapping(uint64_t* vpn_slicing, uint64_t* new_pt, uint64_t ppn){
    // Helper function for tester_page_table_update()
    // new_pt - the address in memory of the page table
    int i;
    uint64_t vpn_slice=0, alloc_page, new_pt_frame_num;
    for (i=0; i<5; i++){
        vpn_slice=vpn_slicing[i];
        if(new_pt[vpn_slice]%2==0){ // Go to pt and check if it's valid (LSB is 1). if not, allocate
            if(i!=4){
                alloc_page = alloc_page_frame();
                new_pt[vpn_slice] = (alloc_page<<12)+1; // change Valid bit to 1
            }
        }
        if(i==4){
            break;
        }
        // Get the address in the current page table where the current VA subset says, and take the page table in it.
        new_pt_frame_num = new_pt[vpn_slice] >> 12;
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
//        new_pt = phys_to_virt(new_pt[vpn_slice]-1);
        // bits 1-11 are always 0! and bit 0 is the VALID thing, which is always 1 in this point, so remove this bit!
    }
    new_pt[vpn_slice] = (ppn<<12)+1; // change Valid bit to 1
}


void tester_destroy_mapping(uint64_t* vpn_slicing, uint64_t* new_pt){
    // Helper function for tester_page_table_update()
    int i;
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2==0){
            return;
        }
        if(i==4){
            break;
        }
        new_pt = phys_to_virt(new_pt[vpn_slice]-1);
    }
    new_pt[vpn_slice]-=1; // change Valid bit to 0
}


void tester_page_table_update(uint64_t pt, uint64_t vpn, uint64_t ppn){
    // An implementation of a working page_table_update() function
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL;
    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat
    if (ppn==NO_MAPPING){
        tester_destroy_mapping(vpn_slicing, new_pt);
    }
    else{
        tester_update_ppn_mapping(vpn_slicing, new_pt, ppn);
    }
}


uint64_t tester_page_table_query(uint64_t pt, uint64_t vpn){
    // An implementation of a working page_table_query() function
    int i;
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t vpn_slice=0, *new_pt=NULL;
    new_pt = phys_to_virt(pt<<12);
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2 == 0){
            return NO_MAPPING;
        }
        if(i==4){
            break;
        }
        new_pt = phys_to_virt(new_pt[vpn_slice]-1); // returns the address in memory
    }
    return (new_pt[vpn_slice])>>12;
}


int test_sanity_check(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests the most basic functionality of the functions */
    if(page_table_query(pt, vpn) != NO_MAPPING){
        printf("basic table query failed NO_MAPPING. \n");
        return EXIT_FAILED;
    }
    page_table_update(pt, vpn, ppn);
    res = page_table_query(pt, vpn);
	if(res != ppn) {
	    printf("basic table query failed after table_update. \n");
	    return EXIT_FAILED;
	}

	page_table_update(pt, vpn, NO_MAPPING);
    res = page_table_query(pt, vpn);
	if(res != NO_MAPPING) {
	    printf("basic table query failed after NO_MAPPING. \n");
	    return EXIT_FAILED;
	}

	return EXIT_SUCCESS;
}

// TESTS FOR page_table_update():

int test_override_mapping(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests a mapping that was overriden with another ppn */
    uint64_t different_ppn = 0xabaa1;

    page_table_update(pt, vpn, ppn);
    res = page_table_query(pt, vpn);
	if(res != ppn) {
	    printf("test_override_mapping failed{1}. \n");
	    return EXIT_FAILED;
	}
	page_table_update(pt, vpn, different_ppn); // a different ppn
    res = page_table_query(pt, vpn);
	if(res != different_ppn) {
	    printf("test_override_mapping failed{2}. \n");
	    return EXIT_FAILED;
	}

	return 0;
}


int test_override_prefix_similar_vpn(uint64_t pt) {
    /* Tests a mapping of an address that shares a prefix with a previously mapped address.
       test if the first vpn is still mapped, in a way that the second didn't overridden its earlier PTE's
    */
    uint64_t ppn = 0xfff;
    uint64_t different_ppn = 0xabaa1;
    uint64_t vpn_prefix = (0x0123456789abc << 12);
    uint64_t vpn = vpn_prefix | 0xabc;
    uint64_t similar_prefix_vpn = vpn_prefix | 0x123;

    page_table_update(pt, vpn, ppn); // map a vpn
	res = page_table_query(pt, vpn); if(page_table_query(pt, vpn) != ppn) {
	    return EXIT_FAILED;
	}
	page_table_update(pt, similar_prefix_vpn, different_ppn); // map a vpn with a similar prefix
	if(page_table_query(pt, similar_prefix_vpn) != different_ppn) {
	    return EXIT_FAILED;
	}
    res = page_table_query(pt, vpn); if(page_table_query(pt, vpn) != ppn) { // check if first vpn not overridden
	    return EXIT_FAILED;
	}
	return EXIT_SUCCESS;
}


int get_leaf_valid_bit(uint64_t pt, uint64_t vpn) {
    // Helper FUNCTION.
    // iterates on the Page Tables, and returns the valid bit of the PPN from the given VPN location
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL, new_pt_frame_num;
    int valid_bit;

    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat
    if(new_pt == NULL) {
            return EXIT_FAILED;
        }
    int i;
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2==0){
            return EXIT_SUCCESS;
        }
        if(i==4){
            break;
        }
        new_pt_frame_num = new_pt[vpn_slice] >> 12; // need to pass to phys_to_virt() without any offset.
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
        if(new_pt == NULL) {
            return EXIT_FAILED;
        }

    }
    valid_bit = new_pt[vpn_slice] % 2;
    return valid_bit;
}

int test_mark_leaf_invalid(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests a mapping that was erased is also marked with VALID_BIT=0 */
    page_table_update(pt, vpn, ppn);
	res = page_table_query(pt, vpn); if(page_table_query(pt, vpn) != ppn) {
	    printf("test_mark_leaf_invalid failed{1}. \n");
	    return EXIT_FAILED;
	}
	page_table_update(pt, vpn, NO_MAPPING);
	res = page_table_query(pt, vpn); if(page_table_query(pt, vpn) != NO_MAPPING) {
	    printf("test_mark_leaf_invalid failed{2}. \n");
	    return EXIT_FAILED;
	}
	// Iterate
	int leaf_valid_bit = get_leaf_valid_bit(pt, vpn);
	if(leaf_valid_bit == 1 || leaf_valid_bit == EXIT_FAILED) { // valid bit wasn't turned off together with NO_MAPPING on #frame.
	    printf("test_mark_leaf_invalid failed{3}. \n");
	    return EXIT_FAILED;
	}

	return EXIT_SUCCESS;
}


int test_root_node_not_zero(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests that root PT wasn't assumed to be page 0, but calling sanity_check with a new root PT */
    uint64_t new_pt = alloc_page_frame();

    if(test_sanity_check(new_pt, vpn, ppn) == EXIT_FAILED) {
        return EXIT_FAILED;
    }
	return EXIT_SUCCESS;
}

// TESTS FOR page_table_query():



int test_unmapped_from_each_level(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests that the function returns a "NO_MAPPING" value where there's some valid nodes in the way */
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL, new_pt_frame_num;
    int i;
    // First map some value that can be traversed.
    tester_page_table_update(pt, vpn, ppn);

    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat then take it's address
    if(new_pt == NULL) {
            return EXIT_FAILED;
        }
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        new_pt[vpn_slice] =  new_pt[vpn_slice] & 0xe ; // only resets the first LSbit.
        res = page_table_query(pt, vpn); if(page_table_query(pt, vpn) != NO_MAPPING) { // check that it fails.
            return EXIT_FAILED;
        }
        new_pt[vpn_slice] =  new_pt[vpn_slice] | 0x1 ; // sets first bit to 1 again.

        if(i==4){
            break;
        }
        new_pt_frame_num = new_pt[vpn_slice] >> 12; // need to pass to phys_to_virt() without any offset.
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
        if(new_pt == NULL) {
            return EXIT_FAILED;
        }
    }
    return EXIT_SUCCESS;
}

int POINTS_DEDUCTION_PER_TEST = 5;

int test_all_tests_combined() {
    uint64_t pt = alloc_page_frame(); // the physical page number of this frame
    int static student_grade = 100;

    if(test_sanity_check(pt, 0xcafe, 0xf00d) == EXIT_FAILED) {
        printf("basic functionality fails. \n");
        return BASIC_FUNC_FAILED;
    }

    if(test_override_mapping(pt, 0xbafb, 0xaa) == EXIT_FAILED) {

        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(test_override_prefix_similar_vpn(pt) == EXIT_FAILED) {
        printf("test_override_prefix_similar_vpn failed. \n");
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(page_table_query(pt, 0x10000f) != NO_MAPPING) {
       printf("test_big_physical_number. \n");
       student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(test_root_node_not_zero(pt, 0x29a, 0xafab) == EXIT_FAILED) {
        printf("test_root_node_not_zero failed. \n");
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    // Tests for page_table_query()
    if(test_unmapped_from_each_level(pt, 0xb5522, 0xa2222) == EXIT_FAILED) {
        printf("test_unmapped_from_each_level failed. \n");
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(test_mark_leaf_invalid(pt, 0x1fa1, 0xabc) == EXIT_FAILED) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    printf("%d\n", student_grade);

    return EXIT_SUCCESS;

}


int main(int argc, char **argv)
{
    if(argc == 1) { // No arguments - run normally!
        return test_all_tests_combined();
    }
    if(argc == 2) { // do sanity test only
        uint64_t pt = alloc_page_frame();
        if(test_sanity_check(pt, 0xcafe, 0xf00d) == EXIT_FAILED) {
            printf("basic functionality fails. \n");
            return BASIC_FUNC_FAILED;
        }
        return EXIT_SUCCESS;
    }
}

