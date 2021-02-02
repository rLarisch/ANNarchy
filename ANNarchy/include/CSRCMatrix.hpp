/*
 *
 *    CSRCMatrix.hpp
 *
 *    This file is part of ANNarchy.
 *
 *    Copyright (C) 2020  Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>,
 *    Julien Vitay <julien.vitay@gmail.com>
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    ANNarchy is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

/**
 *  @brief      Implementation of the compressed sparse row and column (CSRC) matrix format.
 *  @details    A detailed explaination of the format can be found e. g. in 
 *              
 *                  Brette, R. and Goodman, D. F. M. (2011). Vectorized algorithms for spiking neural network
 *                  simulation. Neural computation, 23(6):1503–1535.
 *
 *              The major idea is to extend the forward view of the CSR format by an backward view to
 *              allow a column-oriented indexing which is required for the spike propagation.
 */
template<typename IT = unsigned int>
class CSRCMatrix: public CSRMatrix<IT> {
protected:
    // CSR inverse
    std::vector<IT> _col_ptr;
    std::vector<IT> _row_idx;
    std::vector<IT> _inv_idx;

public:
    CSRCMatrix(const IT num_rows, const IT num_columns) : CSRMatrix<IT>(num_rows, num_columns) {

    }

    void init_matrix_from_lil(std::vector<IT> row_indices, std::vector< std::vector<IT> > column_indices) {
    #ifdef _DEBUG
        std::cout << "CSRCMatrix::init_matrix_from_lil():" << std::endl;
    #endif
        // create forward view
        static_cast<CSRMatrix<IT>*>(this)->init_matrix_from_lil(row_indices, column_indices);

        // compute backward view
        inverse_connectivity_matrix();
    }

    //
    //  Connectivity patterns
    //
    void fixed_number_pre_pattern(std::vector<IT> post_ranks, std::vector<IT> pre_ranks, unsigned int nnz_per_row, std::mt19937& rng) {
        clear();
    #ifdef _DEBUG
        std::cout << "CSRCMatrix::fixed_number_pre_pattern():" << std::endl;
    #endif
        // Generate post_to_pre LIL
        auto lil_mat = new LILMatrix<IT>(this->num_rows_, this->num_columns_);
        lil_mat->fixed_number_pre_pattern(post_ranks, pre_ranks, nnz_per_row, rng);

        // Generate CSRC_T from this LIL
        init_matrix_from_lil(lil_mat->get_post_rank(), lil_mat->get_pre_ranks());

        // cleanup
        delete lil_mat;
    }

    void fixed_probability_pattern(std::vector<IT> post_ranks, std::vector<IT> pre_ranks, double p, bool allow_self_connections, std::mt19937& rng) {
        clear();
    #ifdef _DEBUG
        std::cout << "CSRCMatrix::fixed_probability_pattern():" << std::endl;
    #endif
        // Generate post_to_pre LIL
        auto lil_mat = new LILMatrix<IT>(this->num_rows_, this->num_columns_);
        lil_mat->fixed_probability_pattern(post_ranks, pre_ranks, p, allow_self_connections, rng);

        // Generate CSRC_T from this LIL
        init_matrix_from_lil(lil_mat->get_post_rank(), lil_mat->get_pre_ranks());

        // cleanup
        delete lil_mat;
    }

    void inverse_connectivity_matrix() {
        //
        // 2-pass algorithm: 1st we compute the inverse connectivity as LIL, 2ndly transform it to CSR
        //
        std::map< IT, std::vector< IT > > inv_post_rank = std::map< IT, std::vector< IT > >();
        std::map< IT, std::vector< IT > > inv_idx = std::map< IT, std::vector< IT > >();

        // iterate over post neurons, post_rank_it encodes the current rank
        for( int i = 0; i < ( this->row_begin_.size()-1); i++ ) {
            int row_begin = this->row_begin_[i];
            int row_end = this->row_begin_[i+1];

            // iterate over synapses, update both result containers
            for( int syn_idx = row_begin; syn_idx < row_end; syn_idx++ ) {
                inv_post_rank[this->col_idx_[syn_idx]].push_back(i);
                inv_idx[this->col_idx_[syn_idx]].push_back(syn_idx);
            }
        }

        //
        // store as CSR
        //
        _col_ptr.clear();
        _row_idx.clear();
        _inv_idx.clear();
        int curr_off = 0;

        // iterate over pre-neurons
        for ( int i = 0; i < this->num_columns_; i++) {
            _col_ptr.push_back( curr_off );
            if ( !inv_post_rank[i].empty() ) {
                _row_idx.insert(_row_idx.end(), inv_post_rank[i].begin(), inv_post_rank[i].end());
                _inv_idx.insert(_inv_idx.end(), inv_idx[i].begin(), inv_idx[i].end());

                curr_off += inv_post_rank[i].size();
            }
        }
        _col_ptr.push_back(curr_off);

        if ( this->num_non_zeros_ != curr_off )
            std::cerr << "Something went wrong: (nb_synapes = " << this->num_non_zeros_ << ") != (curr_off = " << curr_off << ")" << std::endl;
    #ifdef _DEBUG_CONN
        std::cout << "Pre to Post:" << std::endl;
        for ( int i = 0; i < this->num_columns_; i++ ) {
            std::cout << i << ": " << col_ptr[i] << " -> " << col_ptr[i+1] << std::endl;
        }
    #endif
    }

    /*
     *  \brief      Destructor
     *  \details    Destroys only components which belongs to backward view.
     */
    ~CSRCMatrix() {
    #ifdef _DEBUG
        std::cout << "CSRCMatrix::~CSRCMatrix()" << std::endl;
    #endif
        clear();
    }

    /**
     * \details     Clear the STL container
     */
    void clear() {
        static_cast<CSRMatrix<IT>*>(this)->clear();
    #ifdef _DEBUG
        std::cout << "CSRCMatrix::clear()" << std::endl;
    #endif
        _col_ptr.clear();
        _col_ptr.shrink_to_fit();
        _row_idx.clear();
        _row_idx.shrink_to_fit();
        _inv_idx.clear();
        _inv_idx.shrink_to_fit();
    }

    /**
     *  \brief      Returns size in bytes for connectivity.
     *  \details    Includes the backward and forward view.
     */
    size_t size_in_bytes() {
        size_t size = 0;

        // forward view of CSR
        size += static_cast<CSRMatrix<IT>*>(this)->size_in_bytes();

        // backward view
        size += _col_ptr.capacity() * sizeof(IT);
        size += _row_idx.capacity() * sizeof(IT);
        size += _inv_idx.capacity() * sizeof(IT);

        return size;
    }
};