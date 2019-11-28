#include <stdlib.h>
#include <stdio.h>
#include "os.h"


void _update_ppn_mapping(uint64_t* vpn_slicing, uint64_t* new_pt, uint64_t ppn){
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


void _destroy_mapping(uint64_t* vpn_slicing, uint64_t* new_pt){
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
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL;
    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat
    if (ppn==NO_MAPPING){
        _destroy_mapping(vpn_slicing, new_pt);
    }
    else{
        _update_ppn_mapping(vpn_slicing, new_pt, ppn);
    }
}

uint64_t tester_page_table_query(uint64_t pt, uint64_t vpn){
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


//