/*
 * pt.c
 *
 *  Created on: 19 Nov 2019
 *      Author: student
 */

#include "os.h"
#include <stdio.h>
#include <inttypes.h>

void page_table_update(uint64_t pt, uint64_t vpn, uint64_t ppn)
{
	uint64_t vpnnew = vpn, vpnCurr = pt, *vpnToCheck, newPage;
	uint64_t vpns[5];
	int count = 0;
	vpns[4] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[3] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[2] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[1] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[0] = vpnnew & (511);
	while(count < 4)
	{
		vpnCurr += vpns[count] * 8;
		vpnToCheck = phys_to_virt(vpnCurr);
		if(((*vpnToCheck) & 1) == 1)
		{
			vpnCurr =  *vpnToCheck >> 12;
		}
		else
		{
			if(ppn == NO_MAPPING)
			{
				return;
			}
			else
			{
				newPage = alloc_page_frame() * 4096;
				*vpnToCheck = ((newPage << 12) | 1);
				vpnCurr = newPage;
			}

		}
		count ++;
	}
	vpnCurr += vpns[count] * 8;
	vpnToCheck = phys_to_virt(vpnCurr);
	if(ppn == NO_MAPPING)
	{
		*vpnToCheck = 0x0;
	}
	else
	{
		*vpnToCheck = (ppn << 12) | 1;
	}
}



uint64_t page_table_query(uint64_t pt, uint64_t vpn)
{
	uint64_t vpnnew = vpn, vpnCurr = pt, *vpnToCheck;
	uint64_t vpns[5];
	int count = 0;
	vpns[4] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[3] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[2] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[1] = vpnnew & (511);
	vpnnew = vpnnew >> 9;
	vpns[0] = vpnnew & (511);
	while(count < 4)
	{
		vpnCurr += vpns[count] * 8;
		vpnToCheck = phys_to_virt(vpnCurr);
		if((*vpnToCheck & 1) == 1)
		{
			vpnCurr =  *vpnToCheck >> 12;
		}
		else
		{
			return NO_MAPPING;
		}
		count ++;
	}
	vpnCurr += vpns[count] * 8;
	vpnToCheck = phys_to_virt(vpnCurr);
	if((*vpnToCheck & 1) ==	0)
	{
		return NO_MAPPING;
	}
	else
	{
		return ((*vpnToCheck) >> 12);
	}
}

