public class MergeCutoff {
    private static void merge(Comparable[] a, Comparable[] aux, int lo, int mid, int hi) {
        assert isSorted(a, lo, mid); 
        assert isSorted(a, mid+1, hi);

        for (int i = lo; i <= hi; i++) {
            aux[i] = a[i];
        }

        int i = lo;   int j = mid + 1;
        for (int k = lo; k <= hi; k ++) {
            if (i > mid) {a[k] = aux[j++];}
            else if (j > hi) {a[k] = aux[i++];}
            else if (less(aux[j], aux[i])) {a[k] = aux[j++];}
            else {a[k] = aux[i++];}
        }

        assert isSorted(a, lo, hi);
    }

    private static void sort(Comparable[] a, Comparable[] aux, int lo, int hi, int cutoff) { // đệ quy 
        if (hi <= lo) return;
        if (hi <= lo + cutoff - 1)
        {
            insertionSort(a, lo, hi);
            return;
        }
        int mid = lo + (hi - lo) / 2;
        sort (a, aux, lo, mid, cutoff);
        sort (a, aux, mid+1, hi, cutoff);
        if (!less(a[mid+1], a[mid])) return;
        merge(a, aux, lo, mid, hi);
    }

    public static void sort(Comparable[] a, int cutoff)
    {
        Comparable[] aux = new Comparable[a.length];
        sort(a, aux, 0, a.length - 1, cutoff);
    }

    private static void insertionSort(Comparable[] a, int lo, int hi) {
    for (int i = lo + 1; i <= hi; i++) {
        for (int j = i; j > lo && less(a[j], a[j - 1]); j--) {
            Comparable swap = a[j];
            a[j] = a[j - 1];
            a[j - 1] = swap;
        }
    }
}

    private static boolean isSorted(Comparable[] a, int lo, int hi) {
        int n = a.length;
        for (int i = lo + 1; i <= hi; i++) {
            if (less(a[i], a[i - 1])) {
                return false;
            } else if (equal(a[i], a[i - 1])) {
                continue;
            }
        }
        return true;
    }

    private static boolean less(Comparable v, Comparable w) {
        return v.compareTo(w) < 0;
    }

    private static boolean equal(Comparable v, Comparable w) {
        return v.compareTo(w) == 0;
    }
}