// src/utils/swal.ts
import Swal from 'sweetalert2';
import type { SweetAlertOptions } from 'sweetalert2';

export function fire(options: SweetAlertOptions) {
  return Swal.fire({
    ...options,
    didOpen: (popup) => {
      // primero ejecutamos tu didOpen si lo hay
      options.didOpen?.(popup);
      // luego forzamos z-index
      document
        .querySelector('.swal2-container')
        ?.setAttribute('style', 'z-index:2000 !important');
    }
  });
}
